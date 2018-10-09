import { withStyles } from "@material-ui/core/styles";
// import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";

import Form from "../../../components/Form";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import { UserError } from "../../../";
import i18n from "../../../i18n";
import CategoryDetailsForm from "../../components/CategoryDetailsForm";
import SeoForm from "../../../components/SeoForm";
import CategoryBackground from "../CategoryBackground";
import CategoryCreateSubcategories from "../CategoryCreateSubcategories";
import Toggle from "../../../components/Toggle";
import CategoryDeleteDialog from "../../components/CategoryDeleteDialog";

import SaveButtonBar, {
  SaveButtonBarState
} from "../../../components/SaveButtonBar/SaveButtonBar";

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

  onSubmit(data: FormData);
  onImageUpload?(event: React.ChangeEvent<any>);

  onBack();
  onDelete();
  saveButtonBarState?: SaveButtonBarState;
}
const decorate = withStyles(theme => ({
  root: {
    display: "grid",
    marginTop: theme.spacing.unit * 2,
    gridGap: theme.spacing.unit * 4 + "px"
  }
}));

export const CategoryCreatePage = decorate<CategoryCreatePageProps>(
  ({
    classes,
    header,
    disabled,
    onSubmit,
    onBack,
    errors: userErrors,
    onImageUpload,
    onDelete,
    saveButtonBarState
  }) => {
    const initialData: FormData = {
      name: "",
      description: "",
      seoTitle: "",
      seoDescription: ""
      // backgroundImage: ""
    };
    return (
      <Toggle>
        {(openedDeleteDialog, { toggle: toggleDeleteDialog }) => (
          <Form onSubmit={onSubmit} initial={initialData} errors={userErrors}>
            {({ data, change, errors, submit, hasChanged }) => (
              <>
                <Container width="lg">
                  <PageHeader title={header} />
                  <div className={classes.root}>
                    <CategoryDetailsForm
                      disabled={disabled}
                      data={data}
                      onChange={change}
                      errors={errors}
                      loading={false}
                    />
                    <CategoryBackground
                      onImageUpload={onImageUpload}
                      disabled={disabled}
                    />
                    <CategoryCreateSubcategories disabled={disabled} />
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
                      disabled={disabled}
                    />{" "}
                    <SaveButtonBar
                      onCancel={onBack}
                      onDelete={toggleDeleteDialog}
                      onSave={submit}
                      labels={{
                        save: i18n.t("Save category"),
                        delete: i18n.t("Delete category")
                      }}
                      state={saveButtonBarState}
                      disabled={disabled || !hasChanged}
                    />
                  </div>
                </Container>
                <CategoryDeleteDialog
                  name={undefined}
                  open={openedDeleteDialog}
                  productCount={undefined}
                  onClose={toggleDeleteDialog}
                  onConfirm={onDelete}
                />
              </>
            )}
          </Form>
        )}
      </Toggle>
    );
  }
);
export default CategoryCreatePage;
