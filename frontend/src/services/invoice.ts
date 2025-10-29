import api from './api';

export interface Invoice {
  id: number;
  invoice_number: string | null;
  invoice_date: string | null;
  amount: number | null;
  due_date: string | null;
  file_name: string;
  file_path: string;
  raw_text: string;
  created_at: string;
  owner_id: number;
}

export const invoiceService = {
  async getInvoices(): Promise<Invoice[]> {
    const response = await api.get<Invoice[]>('/invoices/');
    return response.data;
  },

  async getInvoice(id: string | number): Promise<Invoice> {
    const response = await api.get<Invoice>(`/invoices/${id}`);
    return response.data;
  },

  async uploadInvoice(file: File): Promise<Invoice> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post<Invoice>('/invoices/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async updateInvoice(id: string | number, data: Partial<Invoice>): Promise<Invoice> {
    const response = await api.put<Invoice>(`/invoices/${id}`, data);
    return response.data;
  },

  async deleteInvoice(id: string | number): Promise<void> {
    await api.delete(`/invoices/${id}`);
  },
};

export default invoiceService;
