import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import DialogContentText from "@material-ui/core/DialogContentText";
import ActionDialog from "../../../components/ActionDialog";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar, {
  SaveButtonBarState
} from "../../../components/SaveButtonBar";
import Toggle from "../../../components/Toggle";
import i18n from "../../../i18n";
import AttributeDetails from "../AttributeDetails/AttributeDetails";
import AttributeValueList from "../AttributeValueList/AttributeValueList";

interface AttributeDetailsPageProps {
  attribute?: {
    id: string;
    name: string;
    values: Array<{
      id: string;
      name: string;
      sortOrder: number;
      slug: string;
    }>;
  };
  disabled: boolean;
  saveButtonBarState: SaveButtonBarState;
  onBack: () => void;
  onDelete: () => void;
  onSubmit: () => void;
}

const decorate = withStyles(theme => ({
  root: {
    display: "grid",
    gridColumnGap: theme.spacing.unit * 2 + "px",
    gridTemplateColumns: "2fr 1fr"
  }
}));
const AttributeDetailsPage = decorate<AttributeDetailsPageProps>(
  ({
    attribute,
    classes,
    disabled,
    saveButtonBarState,
    onBack,
    onDelete,
    onSubmit
  }) => (
    <Toggle>
      {(openedDeleteDialog, { toggle: toggleDeleteDialog }) => (
        <Form
          initial={{
            name: attribute && attribute.name,
            values: attribute && attribute.values
          }}
          onSubmit={onSubmit}
          key={JSON.stringify(attribute)}
        >
          {({ change, data, hasChanged, submit }) => (
            <>
              <Container width="md">
                <PageHeader
                  title={attribute ? attribute.name : undefined}
                  onBack={onBack}
                />
                <div className={classes.root}>
                  <div>
                    <AttributeDetails
                      data={data}
                      disabled={disabled}
                      onChange={change}
                    />
                    <AttributeValueList
                      disabled={disabled}
                      loading={!attribute || !attribute.values}
                      values={data.values}
                      onChange={change}
                    />
                  </div>
                </div>
                <SaveButtonBar
                  onCancel={onBack}
                  onDelete={toggleDeleteDialog}
                  state={saveButtonBarState}
                  disabled={disabled || !hasChanged}
                  onSave={submit}
                />
              </Container>
              {attribute && (
                <ActionDialog
                  open={openedDeleteDialog}
                  variant="delete"
                  onConfirm={onDelete}
                  onClose={toggleDeleteDialog}
                  title={i18n.t("Remove attribute")}
                >
                  <DialogContentText
                    dangerouslySetInnerHTML={{
                      __html: i18n.t(
                        "Are you sure you want to remove <strong>{{ name }}</strong>?",
                        { name: attribute.name }
                      )
                    }}
                  />
                </ActionDialog>
              )}
            </>
          )}
        </Form>
      )}
    </Toggle>
  )
);
AttributeDetailsPage.displayName = "AttributeDetailsPage";
export default AttributeDetailsPage;
