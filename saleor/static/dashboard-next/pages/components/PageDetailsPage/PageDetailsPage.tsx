import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import DeleteIcon from "@material-ui/icons/Delete";
import * as React from "react";

import { Container } from "../../../components/Container";
import Form, { FormProps } from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import Toggle from "../../../components/Toggle";
import PageContent from "../PageContent";
import PageDeleteDialog from "../PageDeleteDialog";
import PageProperties from "../PageProperties";

interface PageInput {
  title: string;
  content: string;
  slug: string;
  availableOn: string;
  isVisible: boolean;
}
interface PageDetailsPageProps {
  page?: PageInput & {
    created?: string;
  };
  errors?: Array<{
    field: string;
    message: string;
  }>;
  disabled?: boolean;
  title?: string;
  onBack?();
  onDelete?();
  onSubmit(data: PageInput);
}

const defaultPage = {
  availableOn: "",
  content: "",
  isVisible: false,
  slug: "",
  title: ""
};
const PageForm: React.ComponentType<FormProps<PageInput>> = Form;
const decorate = withStyles(theme => ({
  root: {
    display: "grid" as "grid",
    gridColumnGap: `${theme.spacing.unit * 2}px`,
    gridTemplateColumns: "3fr 1fr"
  }
}));
const PageDetailsPage = decorate<PageDetailsPageProps>(
  ({ classes, errors, disabled, page, title, onBack, onDelete, onSubmit }) => (
    <PageForm
      key={page ? "ready" : "loading"}
      initial={page ? page : defaultPage}
      onSubmit={onSubmit}
    >
      {({ change, data, submit }) => (
        <Toggle>
          {(opened, { toggle: togglePageDeleteDialog }) => (
            <Container width="md">
              <>
                <PageHeader onBack={onBack} title={title}>
                  {!!onDelete && (
                    <IconButton onClick={togglePageDeleteDialog}>
                      <DeleteIcon />
                    </IconButton>
                  )}
                </PageHeader>
                <div className={classes.root}>
                  <div>
                    <PageContent
                      loading={disabled}
                      onChange={change}
                      content={data.content}
                      title={data.title}
                    />
                  </div>
                  <div>
                    <PageProperties
                      availableOn={data.availableOn}
                      created={page ? page.created : undefined}
                      isVisible={data.isVisible}
                      loading={disabled}
                      onChange={change}
                      slug={data.slug}
                    />
                  </div>
                </div>
                <SaveButtonBar
                  state={disabled ? "disabled" : "default"}
                  onSave={submit}
                />
                {!!onDelete &&
                  !disabled && (
                    <PageDeleteDialog
                      opened={opened}
                      onConfirm={onDelete}
                      onClose={togglePageDeleteDialog}
                      title={page.title}
                    />
                  )}
              </>
            </Container>
          )}
        </Toggle>
      )}
    </PageForm>
  )
);
export default PageDetailsPage;
