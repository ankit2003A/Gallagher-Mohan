import { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Table, Alert, Button } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { invoiceService, Invoice } from '../services/invoice';
import Spinner from '../components/ui/Spinner';

function getStatusBadgeColor(status: string): string {
  switch (status?.toLowerCase()) {
    case 'paid':
      return 'success';
    case 'pending':
      return 'warning';
    case 'overdue':
      return 'danger';
    default:
      return 'secondary';
  }
}

export default function Dashboard() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchInvoices();
  }, []);

  const fetchInvoices = async () => {
    try {
      const data = await invoiceService.getInvoices();
      setInvoices(data);
    } catch (err) {
      setError('Failed to fetch invoices');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      await invoiceService.uploadInvoice(file);
      await fetchInvoices(); // Refresh the list
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload invoice');
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return <Spinner className="mt-5" />;
  }

  return (
    <Container>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1>Dashboard</h1>
        <div>
          <input
            type="file"
            id="file-upload"
            style={{ display: 'none' }}
            accept=".pdf,.jpg,.jpeg,.png"
            onChange={handleFileUpload}
            disabled={uploading}
          />
          <Button
            variant="primary"
            onClick={() => document.getElementById('file-upload')?.click()}
            disabled={uploading}
          >
            {uploading ? 'Uploading...' : 'Upload Invoice'}
          </Button>
        </div>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      <Row className="mb-4">
        <Col>
          <Card>
            <Card.Body>
              <Card.Title>Recent Invoices</Card.Title>
              <div className="table-responsive">
                <Table striped hover>
                  <thead>
                    <tr>
                      <th>Invoice #</th>
                      <th>File Name</th>
                      <th>Amount</th>
                      <th>Invoice Date</th>
                      <th>Due Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {invoices.length > 0 ? (
                      invoices.map((invoice) => (
                        <tr key={invoice.id}>
                          <td>
                            <Link to={`/invoices/${invoice.id}`}>
                              {invoice.invoice_number || 'N/A'}
                            </Link>
                          </td>
                          <td>{invoice.file_name}</td>
                          <td>{invoice.amount ? `$${invoice.amount.toFixed(2)}` : '-'}</td>
                          <td>
                            {invoice.invoice_date 
                              ? new Date(invoice.invoice_date).toLocaleDateString() 
                              : '-'}
                          </td>
                          <td>
                            {invoice.due_date 
                              ? new Date(invoice.due_date).toLocaleDateString() 
                              : '-'}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={5} className="text-center">
                          No invoices found. Upload an invoice to get started!
                        </td>
                      </tr>
                    )}
                  </tbody>
                </Table>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}
