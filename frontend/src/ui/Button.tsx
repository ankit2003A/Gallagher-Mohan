import { Button as BsButton, Spinner } from 'react-bootstrap';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading?: boolean;
  variant?: string;
  children: React.ReactNode;
}

function Button({ isLoading, children, ...props }: ButtonProps) {
  return (
    <BsButton disabled={isLoading} {...props}>
      {isLoading ? (
        <>
          <Spinner
            as="span"
            animation="border"
            size="sm"
            role="status"
            aria-hidden="true"
            className="me-2"
          />
          Loading...
        </>
      ) : (
        children
      )}
    </BsButton>
  );
}

export default Button;
