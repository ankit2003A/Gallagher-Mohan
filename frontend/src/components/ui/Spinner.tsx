import { Spinner as BsSpinner } from 'react-bootstrap';

interface SpinnerProps {
  size?: 'sm';
  className?: string;
}

function Spinner({ size, className = '' }: SpinnerProps) {
  return (
    <div className={`d-flex justify-content-center ${className}`}>
      <BsSpinner animation="border" role="status" size={size}>
        <span className="visually-hidden">Loading...</span>
      </BsSpinner>
    </div>
  );
}

export default Spinner;
