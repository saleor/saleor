import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import TextField from "@material-ui/core/TextField";
import * as CRC from "crc-32";
import * as React from "react";

import { Container } from "../../../components/Container";
import Form from "../../../components/Form";
import FormSpacer from "../../../components/FormSpacer";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar, {
  SaveButtonBarState
} from "../../../components/SaveButtonBar";
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
  saveButtonBarState?: SaveButtonBarState;
  onBack?();
  onSubmit?();
}

const CustomerEditPage: React.StatelessComponent<CustomerEditPageProps> = ({
  customer,
  disabled,
  errors,
  onBack,
  onSubmit,
  saveButtonBarState,
  variant
}) => {
  const errorList: { [key: string]: string } = errors
    ? errors.reduce((acc, curr) => {
        acc[curr.field] = curr.message;
        return acc;
      }, {})
    : {};
  return (
    <Form
      initial={{
        email: customer && customer.email ? customer.email : "",
        note:
          customer && customer.note !== undefined && customer.note !== null
            ? customer.note
            : ""
      }}
      key={customer ? CRC.str(JSON.stringify(customer)) : "loading"}
    >
      {({ change, data, hasChanged }) => (
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
                multiline
                rows={10}
              />
            </CardContent>
          </Card>
          <SaveButtonBar
            disabled={disabled || !onSubmit || !hasChanged}
            state={saveButtonBarState}
            onCancel={onBack}
            onSave={onSubmit}
          />
        </Container>
      )}
    </Form>
  );
};
export default CustomerEditPage;
