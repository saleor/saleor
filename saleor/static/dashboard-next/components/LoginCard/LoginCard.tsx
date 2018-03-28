import Card, { CardProps } from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import CardHeader from "@material-ui/core/CardHeader";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import { FormActions } from "../../components/Form";
import i18n from "../../i18n";

export interface LoginCardProps extends CardProps {
  email: string;
  errors: Array<{
    field: string;
    message: string;
  }>;
  password: string;
  onCancel?();
  onChange?(event: React.ChangeEvent<any>);
  onSubmit?(event: React.FormEvent<any>);
}

const LoginCard: React.StatelessComponent<LoginCardProps> = ({
  email,
  errors,
  onCancel,
  onChange,
  onSubmit,
  password,
  ...cardProps
}) => {
  const errorMap: { [key: string]: string } = errors.reduce((acc, curr) => {
    acc[curr.field] = curr.message;
    return acc;
  }, {});
  return (
    <Card {...cardProps}>
      <CardHeader title={i18n.t("Authenticate", { context: "title" })} />
      <CardContent>
        <TextField
          autoFocus
          fullWidth
          autoComplete="username"
          error={!!errorMap.email}
          helperText={errorMap.email}
          label={i18n.t("Email", { context: "form" })}
          name="email"
          onChange={onChange}
          value={email}
        />
        <TextField
          fullWidth
          autoComplete="current-password"
          error={!!errorMap.password}
          helperText={errorMap.password}
          label={i18n.t("Password")}
          name="password"
          onChange={onChange}
          type="password"
          value={password}
        />
      </CardContent>
      <FormActions
        onCancel={onCancel}
        onSubmit={onSubmit}
        submitLabel={i18n.t("Log in", { context: "button" })}
      />
    </Card>
  );
};

export default LoginCard;
