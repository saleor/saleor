import * as React from "react";

interface ErrorProps {
  error: string;
}

export const Error: React.FC<ErrorProps> = ({ error }) => <>{error}</>;
export default Error;
