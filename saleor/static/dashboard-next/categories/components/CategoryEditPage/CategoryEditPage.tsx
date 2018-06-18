import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import { Container } from "../../../components/Container";
import Form from "../../../components/Form";
import { FormSpacer } from "../../../components/FormSpacer";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import i18n from "../../../i18n";

interface CategoryEditPageProps {
  category?: {
    description: string;
    name: string;
  };
  errors?: Array<{
    field: string;
    message: string;
  }>;
  disabled?: boolean;
  variant?: "add" | "edit";
  onBack?();
  onSubmit(data: any);
}

const CategoryEditPage: React.StatelessComponent<CategoryEditPageProps> = ({
  category,
  errors,
  disabled,
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
        description: category ? category.description : "",
        name: category ? category.name : ""
      }}
      onSubmit={onSubmit}
      key={category === undefined ? "loading" : "ready"}
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
                disabled={disabled}
                value={data && data.name}
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
                disabled={disabled}
                value={data && data.description}
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
          <SaveButtonBar
            state={disabled ? "disabled" : "default"}
            onSave={submit}
          />
        </Container>
      )}
    </Form>
  );
};
export default CategoryEditPage;
