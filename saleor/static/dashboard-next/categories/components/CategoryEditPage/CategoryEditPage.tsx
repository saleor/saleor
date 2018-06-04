import Card, { CardContent } from "material-ui/Card";
import * as React from "react";

import TextField from "material-ui/TextField";
import { Container } from "../../../components/Container";
import Form from "../../../components/Form";
import { FormSpacer } from "../../../components/FormSpacer";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import i18n from "../../../i18n";

interface CategoryEditPageProps {
  description: string;
  errors?: Array<{
    field: string;
    message: string;
  }>;
  loading?: boolean;
  name: string;
  variant?: "add" | "edit";
  onBack?();
  onSubmit(data: any);
}

const CategoryEditPage: React.StatelessComponent<CategoryEditPageProps> = ({
  description,
  errors,
  loading,
  name,
  variant,
  onBack,
  onSubmit
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
        description,
        name
      }}
      onSubmit={onSubmit}
    >
      {({ change, data, submit }) => (
        <Container width="md">
          <PageHeader
            onBack={onBack}
            title={
              variant === "add"
                ? i18n.t("Add category")
                : i18n.t("Edit category")
            }
          />
          <Card>
            <CardContent>
              <TextField
                autoFocus
                fullWidth
                disabled={loading}
                value={data.name}
                error={!!errorList.name}
                helperText={errorList.name}
                label={i18n.t("Name", { context: "category" })}
                name="name"
                onChange={change}
              />
              <FormSpacer />
              <TextField
                fullWidth
                multiline
                disabled={loading}
                value={data.description}
                error={!!errorList.description}
                helperText={
                  errorList.description ||
                  i18n.t("Optional", { context: "field" })
                }
                label={i18n.t("Description")}
                name="description"
                onChange={change}
              />
            </CardContent>
          </Card>
          <SaveButtonBar disabled={loading} onBack={onBack} onSave={submit} />
        </Container>
      )}
    </Form>
  );
};
export default CategoryEditPage;
