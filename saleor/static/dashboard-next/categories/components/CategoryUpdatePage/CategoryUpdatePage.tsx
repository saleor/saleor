import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";

import CategoryDetailsForm from "../../components/CategoryDetailsForm";
import Form from "../../../components/Form";

// import Card from "@material-ui/core/Card";
// import Button from "@material-ui/core/Button";
// import CardContent from "@material-ui/core/CardContent";
// import AddPhotoIcon from "@material-ui/icons/AddAPhoto";
// import Typography from "@material-ui/core/Typography";
// import CardTitle from "../../../components/CardTitle";

// import i18n from "../../../i18n";

interface CategoryUpdatePageProps {
  header: string;

  //CategoryDetailsForm
  category: {
    SeoDescription: string;
    SeoTitle: string;
    name: string;
    description: string;
  };
}

const decorate = withStyles(theme => ({
  root: {
    display: "grid",
    marginTop: theme.spacing.unit * 2,
    gridGap: theme.spacing.unit * 4 + "px"
  }
}));

export const CategoryUpdatePage = decorate<CategoryUpdatePageProps>(
  ({ classes, header, category }) => {
    const initialData = category
      ? {
          SeoDescription: category.SeoDescription,
          SeoTitle: category.SeoTitle,
          name: category.name,
          description: category.description
        }
      : {
          SeoDescription: "",
          SeoTitle: "",
          description: "",
          name: ""
        };
    return (
      <Form initial={initialData}>
        {({ data }) => (
          <Container width="lg">
            <PageHeader title={header} />
            <div className={classes.root}>
              <CategoryDetailsForm
                disabled={false}
                data={category}
                onChange={() => undefined}
                errors={undefined}
              />
            </div>
          </Container>
        )}
      </Form>
    );
  }
);
export default CategoryUpdatePage;
