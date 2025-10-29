import { useState } from 'react';
import { Form, Card, Alert, InputGroup } from 'react-bootstrap';
import { Eye, EyeSlash } from 'react-bootstrap-icons';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Button from '../components/ui/Button';
import * as yup from 'yup';
import { Formik } from 'formik';

const loginSchema = yup.object().shape({
  email: yup.string().email('Invalid email').required('Email is required'),
  password: yup.string().required('Password is required'),
});

export default function Login() {
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="d-flex align-items-center justify-content-center min-vh-100">
      <div className="w-100" style={{ maxWidth: '400px' }}>
        <Card>
          <Card.Body>
            <h2 className="text-center mb-4">Log In</h2>
            {error && <Alert variant="danger">{error}</Alert>}
            <Formik
              initialValues={{ email: '', password: '' }}
              validationSchema={loginSchema}
              onSubmit={async (values, { setSubmitting }) => {
                try {
                  setError('');
                  await login(values.email, values.password);
                  navigate('/');
                } catch (err) {
                  setError('User not found. Please register first.');
                } finally {
                  setSubmitting(false);
                }
              }}
            >
              {({ handleSubmit, handleChange, values, errors, touched, isSubmitting }) => (
                <Form onSubmit={handleSubmit}>
                  <Form.Group className="mb-3" controlId="email">
                    <Form.Label>Email</Form.Label>
                    <Form.Control
                      type="email"
                      name="email"
                      value={values.email}
                      onChange={handleChange}
                      isInvalid={touched.email && !!errors.email}
                    />
                    <Form.Control.Feedback type="invalid">
                      {errors.email}
                    </Form.Control.Feedback>
                  </Form.Group>

                  <Form.Group className="mb-3" controlId="password">
                    <Form.Label>Password</Form.Label>
                    <InputGroup>
                      <Form.Control
                        type={showPassword ? 'text' : 'password'}
                        name="password"
                        value={values.password}
                        onChange={handleChange}
                        isInvalid={touched.password && !!errors.password}
                      />
                      <InputGroup.Text 
                        onClick={() => setShowPassword(!showPassword)}
                        style={{ cursor: 'pointer' }}
                        className="bg-white"
                      >
                        {showPassword ? <EyeSlash /> : <Eye />}
                      </InputGroup.Text>
                      <Form.Control.Feedback type="invalid">
                        {errors.password}
                      </Form.Control.Feedback>
                    </InputGroup>
                  </Form.Group>

                  <Button
                    type="submit"
                    className="w-100"
                    isLoading={isSubmitting}
                  >
                    Log In
                  </Button>
                </Form>
              )}
            </Formik>
          </Card.Body>
        </Card>
        <div className="w-100 text-center mt-2">
          Need an account? <Link to="/register">Sign Up</Link>
        </div>
      </div>
    </div>
  );
}
