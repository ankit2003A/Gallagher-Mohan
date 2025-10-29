import os
import shutil
import uuid
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import logging

from . import models, schemas
from .database import engine, get_db
from .services import auth, ocr, llm
from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Invoice Processing API",
    description="API for extracting and managing invoice data using OCR and LLM",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for simplicity. Adjust for production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# User registration endpoint
@app.post("/users/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account.
    """
    # Check if user already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_active=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
    
# Create uploads directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Auth endpoints
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Provides an access token for an authenticated user.
    """
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account.
    """
    db_user = auth.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return auth.create_user(db=db, user=user)

# Invoice endpoints
@app.post("/invoices/upload/", response_model=schemas.Invoice)
async def upload_invoice(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload an invoice, process it with OCR/LLM, and save it to the database.
    """
    file_path = "" # Initialize file_path to ensure it's in scope for error handling
    try:
        # Save uploaded file
        file_ext = os.path.splitext(file.filename)[1]
        file_name = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process the file
        logger.info(f"Extracting text from {file_path}")
        raw_text = ocr.extract_text(file_path)
        
        if not raw_text or not raw_text.strip():
             logger.warning(f"No text extracted from {file.filename}")
             raise HTTPException(status_code=400, detail="No text could be extracted from the uploaded file.")

        logger.info(f"Extracting structured data using LLM for {file.filename}")
        invoice_data = llm.extract_invoice_data(raw_text)
        
        # Convert date strings from Pydantic model to date objects for SQLAlchemy
        invoice_data_dict = invoice_data.dict()
        
        if invoice_data_dict.get("invoice_date"):
            invoice_data_dict["invoice_date"] = datetime.strptime(
                invoice_data_dict["invoice_date"], "%Y-%m-%d"
            ).date()
        
        if invoice_data_dict.get("due_date"):
            invoice_data_dict["due_date"] = datetime.strptime(
                invoice_data_dict["due_date"], "%Y-%m-%d"
            ).date()
        
        # Save to database
        db_invoice = models.Invoice(
            file_name=file.filename,
            file_path=file_path,
            raw_text=raw_text,
            owner_id=current_user.id,
            **invoice_data_dict  # Use the converted dictionary
        )
        
        db.add(db_invoice)
        db.commit()
        db.refresh(db_invoice)
        logger.info(f"Successfully processed and saved invoice {db_invoice.id}")
        return db_invoice
        
    except Exception as e:
        logger.error(f"Failed to upload invoice for user {current_user.email}: {e}", exc_info=True)
        # Clean up the saved file if an error occurs
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        
        if isinstance(e, HTTPException):
            raise # Re-raise HTTPException directly
            
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/invoices/", response_model=List[schemas.Invoice])
def get_invoices(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of invoices for the current user.
    """
    return db.query(models.Invoice)\
        .filter(models.Invoice.owner_id == current_user.id)\
        .offset(skip)\
        .limit(limit)\
        .all()

@app.get("/invoices/{invoice_id}", response_model=schemas.Invoice)
def get_invoice(
    invoice_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific invoice by its ID.
    """
    invoice = db.query(models.Invoice)\
        .filter(
            models.Invoice.id == invoice_id,
            models.Invoice.owner_id == current_user.id
        )\
        .first()
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

# Health check
@app.get("/health")
async def health_check():
    """
    A simple health check endpoint.
    """
    return {"status": "healthy"}

# Admin endpoints
@app.get("/admin/users/", response_model=List[schemas.User])
async def get_all_users(
    current_user: models.User = Depends(auth.get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get all users (admin only)
    """
    return db.query(models.User).all()


@app.get("/admin/invoices/", response_model=List[schemas.Invoice])
async def get_all_invoices(
    current_user: models.User = Depends(auth.get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get all invoices (admin only)
    """
    return db.query(models.Invoice).all()


@app.patch("/admin/users/{user_id}/toggle-admin", response_model=schemas.User)
async def toggle_admin_status(
    user_id: int,
    current_user: models.User = Depends(auth.get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Toggle admin status of a user (admin only)
    """
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own admin status"
        )
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_admin = not user.is_admin
    db.commit()
    db.refresh(user)
    return user


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with a welcome message.
    """
    return {
        "message": "Welcome to Invoice Processing API",
        "docs": "/docs"
    }


