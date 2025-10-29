export interface User {
  id: string;
  email: string;
  // Add other user properties as needed
}

export interface Invoice {
  id: string;
  invoice_number: string;
  vendor_name: string;
  amount: number;
  date: string;
  due_date: string;
  status: string;
  // Add more fields as needed
}
