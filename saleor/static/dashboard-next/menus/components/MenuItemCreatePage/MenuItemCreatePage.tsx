import Button from "@material-ui/core/Button";
import { withStyles } from "@material-ui/core/styles";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import { MenuItemInput, MenuItemLinkedObjectType } from "../..";
import { Container } from "../../../components/Container";
import Form from "../../../components/Form";
import SaveButtonBar, {
  SaveButtonBarState
} from "../../../components/SaveButtonBar";
import i18n from "../../../i18n";
import MenuItemProperties from "../MenuItemProperties";

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
      {({ change, data, hasChanged, submit }) => {
        const handleSubmenuAdd = () =>
          change({
            target: {
              name: "children",
              value: [...data.children, initialForm]
            }
          } as any);
        const handleSubmenuChange = (submenu: number) => (
          event: React.ChangeEvent<any>
        ) => {
          const newData = data.children;
          newData[submenu] = {
            ...data.children[submenu],
            [event.target.name]: event.target.value
          };
          change({
            target: {
              name: "children",
              value: newData
            }
          } as any);
        };
        return (
          <Container width="md">
            <MenuItemProperties
              disabled={disabled}
              errors={{}}
              menuItem={data}
              onChange={change}
            />
            {data.children.map((_, submenuIndex) => (
              <MenuItemProperties
                disabled={disabled}
                errors={{}}
                menuItem={data.children[submenuIndex]}
                onChange={handleSubmenuChange(submenuIndex)}
              />
            ))}
            <Button
              className={classes.addButton}
              color="secondary"
              onClick={handleSubmenuAdd}
            >
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
        );
      }}
    </Form>
  )
);
MenuItemCreatePage.displayName = "MenuItemCreatePage";
export default MenuItemCreatePage;
