import DeleteIcon from "@material-ui/icons/Delete";
import IconButton from "material-ui/IconButton";
import { withStyles } from "material-ui/styles";
import * as React from "react";

import { Container } from "../../../components/Container";
import Form, { FormProps } from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import Toggle from "../../../components/Toggle";
import i18n from "../../../i18n";
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
  loading?: boolean;
  title?: string;
  onBack?();
  onDelete?();
  onSubmit(data: PageInput);
}

const PageForm: React.ComponentType<FormProps<PageInput>> = Form;
const decorate = withStyles(theme => ({
  root: {
    display: "grid" as "grid",
    gridColumnGap: `${theme.spacing.unit * 2}px`,
    gridTemplateColumns: "3fr 1fr"
  }
}));
const PageDetailsPage = decorate<PageDetailsPageProps>(
  ({ classes, errors, loading, page, title, onBack, onDelete, onSubmit }) => (
    <PageForm initial={page} onSubmit={onSubmit}>
      {({ change, data, submit }) => (
        <Toggle>
          {(opened, { toggle: togglePageDeleteDialog }) => (
            <Container width="md">
              <>
                <PageHeader
                  onBack={onBack}
                  title={title || i18n.t("Add page", { context: "title" })}
                >
                  {!!onDelete && (
                    <IconButton onClick={togglePageDeleteDialog}>
                      <DeleteIcon />
                    </IconButton>
                  )}
                </PageHeader>
                <div className={classes.root}>
                  <div>
                    <PageContent
                      loading={loading}
                      onChange={change}
                      content={loading ? "" : data.content}
                      title={loading ? "" : data.title}
                    />
                  </div>
                  <div>
                    <PageProperties
                      availableOn={loading ? "" : data.availableOn}
                      created={loading ? "" : page.created}
                      isVisible={loading ? false : data.isVisible}
                      loading={loading}
                      onChange={change}
                      slug={loading ? "" : data.slug}
                    />
                  </div>
                </div>
                <SaveButtonBar onBack={onBack} onSave={submit} />
                {!!onDelete &&
                  !loading && (
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
