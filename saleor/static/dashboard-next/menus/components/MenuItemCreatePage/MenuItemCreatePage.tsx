import Button from "@material-ui/core/Button";
import { withStyles } from "@material-ui/core/styles";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import { MenuItemLinkedObjectType } from "../..";
import { Container } from "../../../components/Container";
import Form from "../../../components/Form";
import SaveButtonBar, {
  SaveButtonBarState
} from "../../../components/SaveButtonBar";
import i18n from "../../../i18n";
import MenuItemProperties from "../MenuItemProperties";

interface MenuItemInput {
  name: string;
  type: MenuItemLinkedObjectType;
  value: string;
}
interface FormData extends MenuItemInput {
  children: MenuItemInput[];
}

interface MenuItemCreatePageProps {
  disabled: boolean;
  saveButtonBarState: SaveButtonBarState;
  onBack: () => void;
  onSubmit: (data: FormData) => void;
}

const decorate = withStyles(theme => ({
  addButton: {
    marginBottom: theme.spacing.unit * 2,
    marginTop: theme.spacing.unit * 2
  }
}));
const initialForm: FormData = {
  children: [],
  name: "",
  type: MenuItemLinkedObjectType.staticUrl,
  value: ""
};
const MenuItemCreatePage = decorate<MenuItemCreatePageProps>(
  ({ classes, disabled, saveButtonBarState, onBack, onSubmit }) => (
    <Form initial={initialForm} onSubmit={onSubmit}>
      {({ change, data, hasChanged, submit }) => (
        <Container width="md">
          <MenuItemProperties
            disabled={disabled}
            errors={{}}
            menuItem={data}
            onChange={change}
          />
          <Button className={classes.addButton} color="secondary">
            {i18n.t("Add menu item", { context: "button" })}
            <AddIcon />
          </Button>
          <SaveButtonBar
            disabled={disabled || !hasChanged}
            state={saveButtonBarState}
            onCancel={onBack}
            onSave={submit}
          />
        </Container>
      )}
    </Form>
  )
);
MenuItemCreatePage.displayName = "MenuItemCreatePage";
export default MenuItemCreatePage;
