import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Container, Card, Button, Spinner, Alert, Row, Col, Badge } from 'react-bootstrap';
import { invoiceService, Invoice } from '../services/invoice';

export default function InvoiceDetail() {
  const { id } = useParams<{ id: string }>();
  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchInvoice = async () => {
      if (!id) return;
      
      try {
        const data = await invoiceService.getInvoice(id);
        setInvoice(data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to fetch invoice details');
      } finally {
        setLoading(false);
      }
    };

    fetchInvoice();
  }, [id]);

  if (loading) {
    return (
      <Container className="mt-5">
        <Spinner />
      </Container>
    );
  }

  if (error) {
    return (
      <Container className="mt-4">
        <Alert variant="danger">{error}</Alert>
        <Button onClick={() => navigate('/')}>Back to Dashboard</Button>
      </Container>
    );
  }

  if (!invoice) {
    return (
      <Container className="mt-4">
        <Alert variant="warning">Invoice not found</Alert>
        <Button onClick={() => navigate('/')}>Back to Dashboard</Button>
      </Container>
    );
  }

  const getStatusBadgeColor = (amount: number | null, dueDate: string | null): string => {
    if (!amount) return 'secondary';
    if (!dueDate) return 'secondary';
    
    const due = new Date(dueDate);
    const now = new Date();
    if (due < now) return 'danger'; // Overdue
    return 'success'; // Paid/Current
  };

  return (
    <Container className="mt-4">
      <Button variant="outline-secondary" onClick={() => navigate('/')} className="mb-3">
        ← Back to Dashboard
      </Button>

      <Card>
        <Card.Header as="h5">
          Invoice #{invoice.invoice_number || 'N/A'}
        </Card.Header>
        <Card.Body>
          <Row>
            <Col md={6}>
              <h6>Basic Information</h6>
              <p><strong>File Name:</strong> {invoice.file_name}</p>
              <p><strong>Invoice Number:</strong> {invoice.invoice_number || 'N/A'}</p>
              <p><strong>Amount:</strong> 
                <span className="ms-2 badge bg-primary">
                  {invoice.amount ? `$${invoice.amount.toFixed(2)}` : 'N/A'}
                </span>
              </p>
            </Col>
            <Col md={6}>
              <h6>Dates</h6>
              <p><strong>Invoice Date:</strong> 
                {invoice.invoice_date 
                  ? new Date(invoice.invoice_date).toLocaleDateString() 
                  : 'N/A'}
              </p>
              <p><strong>Due Date:</strong> 
                {invoice.due_date 
                  ? new Date(invoice.due_date).toLocaleDateString() 
                  : 'N/A'}
              </p>
              <p><strong>Created:</strong> 
                {new Date(invoice.created_at).toLocaleDateString()}
              </p>
              <p>
                <strong>Status:</strong>{' '}
                <Badge bg={getStatusBadgeColor(invoice.amount, invoice.due_date)}>
                  {invoice.amount ? 'Active' : 'Pending'}
                </Badge>
              </p>
            </Col>
          </Row>

          <hr />

          <h6>Raw Text Extracted</h6>
          <Card className="bg-light">
            <Card.Body style={{ maxHeight: '300px', overflow: 'auto' }}>
              <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
                {invoice.raw_text || 'No text extracted'}
              </pre>
            </Card.Body>
          </Card>

          <div className="mt-4">
            <Button variant="primary" className="me-2" onClick={() => window.print()}>
              Print
            </Button>
            <Button variant="outline-danger" onClick={() => navigate('/')}>
              Close
            </Button>
          </div>
        </Card.Body>
      </Card>
    </Container>
  );
}
