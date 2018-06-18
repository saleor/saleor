import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import { Container } from "../../../components/Container";
import Form from "../../../components/Form";
import FormSpacer from "../../../components/FormSpacer";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import i18n from "../../../i18n";

interface CustomerEditPageProps {
  customer?: {
    id: string;
    email: string;
    note: string;
  };
  disabled?: boolean;
  errors?: Array<{
    field: string;
    message: string;
  }>;
  variant: "add" | "edit";
  onBack?();
  onSubmit?();
}

const decorate = withStyles(theme => ({ root: {} }));
const CustomerEditPage = decorate<CustomerEditPageProps>(
  ({ classes, customer, disabled, errors, variant, onBack, onSubmit }) => {
    const errorList: { [key: string]: string } = errors
      ? errors.reduce((acc, curr) => {
          acc[curr.field] = curr.message;
          return acc;
        }, {})
      : {};
    return (
      <Form
        initial={{
          email: customer ? customer.email : "",
          note: customer ? customer.note : ""
        }}
        key={customer === undefined ? "loading" : "ready"}
      >
        {({ change, data, submit }) => (
          <Container width="md">
            <PageHeader
              title={
                variant === "add"
                  ? i18n.t("Add customer")
                  : i18n.t("Edit customer")
              }
              onBack={onBack}
            />
            <Card>
              <CardContent>
                <TextField
                  disabled={disabled}
                  error={!!errorList.email}
                  fullWidth
                  helperText={errorList.email}
                  label={i18n.t("E-mail")}
                  name="email"
                  onChange={change}
                  value={data.email}
                />
                <FormSpacer />
                <TextField
                  disabled={disabled}
                  error={!!errorList.note}
                  fullWidth
                  helperText={
                    errorList.note ? errorList.note : i18n.t("Optional")
                  }
                  label={i18n.t("Note")}
                  name="note"
                  onChange={change}
                  value={data.note}
                />
              </CardContent>
            </Card>
            <SaveButtonBar
              state={disabled ? "disabled" : "default"}
              onSave={onSubmit}
            />
          </Container>
        )}
      </Form>
    );
  }
);
export default CustomerEditPage;
