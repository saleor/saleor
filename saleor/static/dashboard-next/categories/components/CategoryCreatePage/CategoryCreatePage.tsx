import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import Form from "../../../components/Form";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import { UserError } from "../../../";

import CategoryDetailsForm from "../../components/CategoryDetailsForm";

interface FormData {
  //CategoryDetailsForm
  description: string;
  name: string;
}

interface CategoryCreatePageProps {
  errors: UserError[];
  header: string;

  disabled: boolean;

  onSubmit?(data: FormData);
}

const decorate = withStyles(theme => ({
  root: {
    display: "grid",
    marginTop: theme.spacing.unit * 2
  }
}));

export const CategoryCreatePage = decorate<CategoryCreatePageProps>(
  ({ header, disabled, onSubmit, errors: userErrors }) => {
    const initialData: FormData = {
      name: "",
      description: ""
    };
    return (
      <Form onSubmit={onSubmit} initial={initialData} errors={userErrors}>
        {({ data, change, errors }) => (
          <Container width="lg">
            <PageHeader title={header} />
            <CategoryDetailsForm
              disabled={disabled}
              data={data}
              onChange={change}
              errors={errors}
            />
          </Container>
        )}
      </Form>
    );
  }
);
export default CategoryCreatePage;
