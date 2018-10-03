import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import Form from "../../../components/Form";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import SeoForm from "../../../components/SeoForm";
import { UserError } from "../../../";
import i18n from "../../../i18n";

import CategoryDetailsForm from "../../components/CategoryDetailsForm";

interface FormData {
  //CategoryDetailsForm
  description: string;
  name: string;

  // SeoForm
  seoTitle: string;
  seoDescription: string;
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
    marginTop: theme.spacing.unit * 2,
    gridGap: theme.spacing.unit * 4 + "px"
  }
}));

export const CategoryCreatePage = decorate<CategoryCreatePageProps>(
  ({ classes, header, disabled, onSubmit, errors: userErrors }) => {
    const initialData: FormData = {
      name: "",
      description: "",
      seoTitle: "",
      seoDescription: ""
    };
    return (
      <Form onSubmit={onSubmit} initial={initialData} errors={userErrors}>
        {({ data, change, errors }) => (
          <Container width="lg">
            <PageHeader title={header} />
            <div className={classes.root}>
              <CategoryDetailsForm
                disabled={disabled}
                data={data}
                onChange={change}
                errors={errors}
              />
              <SeoForm
                helperText={i18n.t(
                  "Add search engine title and description to make this product easier to find"
                )}
                title={data.seoTitle}
                titlePlaceholder={data.name}
                description={data.seoDescription}
                descriptionPlaceholder={data.description}
                loading={disabled}
                onChange={change}
              />
            </div>
          </Container>
        )}
      </Form>
    );
  }
);
export default CategoryCreatePage;
