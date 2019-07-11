import React from "react";

export interface IProps extends React.InputHTMLAttributes<any> {
  contentLeft?: React.ReactNode;
  contentRight?: React.ReactNode;
  error?: boolean;
  value: React.InputHTMLAttributes<any>["value"];
  label?: string;
}
