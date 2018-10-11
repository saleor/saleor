import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import { CardSpacer } from "../../../components/CardSpacer";
import Form from "../../../components/Form";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import { UserError } from "../../../";
import i18n from "../../../i18n";
import CategoryDetailsForm from "../../components/CategoryDetailsForm";
import SeoForm from "../../../components/SeoForm";
import Toggle from "../../../components/Toggle";
import ActionDialog from "../../../components/ActionDialog";
import DialogContentText from "@material-ui/core/DialogContentText";

import SaveButtonBar, {
  SaveButtonBarState
} from "../../../components/SaveButtonBar/SaveButtonBar";

interface FormData {
  description: string;
  name: string;
  seoTitle: string;
  seoDescription: string;
}

export interface CategoryCreatePageProps {
  errors: UserError[];
  header: string;
  disabled: boolean;
  onSubmit(data: FormData);
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
    header,
    disabled,
    onSubmit,
    onBack,
    errors: userErrors,
    onDelete,
    saveButtonBarState
  }) => {
    const initialData: FormData = {
      name: "",
      description: "",
      seoTitle: "",
      seoDescription: ""
    };
    return (
      <Toggle>
        {(openedDeleteDialog, { toggle: toggleDeleteDialog }) => (
          <Form onSubmit={onSubmit} initial={initialData} errors={userErrors}>
            {({ data, change, errors, submit, hasChanged }) => (
              <>
                <Container width="lg">
                  <PageHeader title={header} />
                  <div>
                    <CategoryDetailsForm
                      disabled={disabled}
                      data={data}
                      onChange={change}
                      errors={errors}
                    />
                    <CardSpacer />
                    <CardSpacer />
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
                <ActionDialog
                  title={i18n.t("Remove category")}
                  open={openedDeleteDialog}
                  onClose={toggleDeleteDialog}
                  onConfirm={onDelete}
                  variant={"delete"}
                >
                  <DialogContentText
                    dangerouslySetInnerHTML={{
                      __html: i18n.t(
                        "Are you sure you want to remove this category"
                      )
                    }}
                  />
                </ActionDialog>
              </>
            )}
          </Form>
        )}
      </Toggle>
    );
  }
);
export default CategoryCreatePage;
