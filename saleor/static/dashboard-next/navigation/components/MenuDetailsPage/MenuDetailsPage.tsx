import Typography from "@material-ui/core/Typography";
import * as React from "react";

import AppHeader from "../../../components/AppHeader";
import CardSpacer from "../../../components/CardSpacer";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import Grid from "../../../components/Grid";
import SaveButtonBar from "../../../components/SaveButtonBar";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { MenuDetails_menu } from "../../types/MenuDetails";
import { MenuItemType } from "../MenuCreateItemDialog";
import MenuItems, { TreeOperation } from "../MenuItems";
import MenuProperties from "../MenuProperties";
import { computeTree } from "./tree";

export interface MenuDetailsFormData {
  name: string;
}

export interface MenuDetailsSubmitData extends MenuDetailsFormData {
  operations: TreeOperation[];
}

export interface MenuDetailsPageProps {
  saveButtonState: ConfirmButtonTransitionState;
  disabled: boolean;
  menu: MenuDetails_menu;
  onBack: () => void;
  onDelete: () => void;
  onItemAdd: () => void;
  onItemClick: (id: string, type: MenuItemType) => void;
  onSubmit: (data: MenuDetailsSubmitData) => Promise<boolean>;
}

const MenuDetailsPage: React.StatelessComponent<MenuDetailsPageProps> = ({
  disabled,
  menu,
  saveButtonState,
  onBack,
  onDelete,
  onItemAdd,
  onItemClick,
  onSubmit
}) => {
  const initialForm: MenuDetailsFormData = {
    name: maybe(() => menu.name, "")
  };

  const [treeOperations, setTreeOperations] = React.useState<TreeOperation[]>(
    []
  );

  const handleSubmit = async (data: MenuDetailsFormData) => {
    if (
      await onSubmit({
        name: data.name,
        operations: treeOperations
      })
    ) {
      setTreeOperations([]);
    }
  };

  const handleChange = (operation: TreeOperation) => {
    if (!!operation) {
      setTreeOperations([...treeOperations, operation]);
    }
  };

  return (
    <Form initial={initialForm} onSubmit={handleSubmit}>
      {({ change, data, hasChanged, submit }) => (
        <Container>
          <AppHeader onBack={onBack}>{i18n.t("Navigation")}</AppHeader>
          <Grid variant="inverted">
            <div>
              <Typography variant="headline">{i18n.t("Navigation")}</Typography>
              <CardSpacer />
              <Typography>
                {i18n.t(
                  "Creating structure of navigation is done via dragging and dropping. Simply create a new menu item and then dragging it into it’s destined place. Take note that you can move items inside one another to create a tree structure"
                )}
              </Typography>
            </div>
            <div>
              <MenuProperties
                data={data}
                disabled={disabled}
                onChange={change}
              />
              <CardSpacer />
              <MenuItems
                canUndo={treeOperations.length > 0}
                items={maybe(() =>
                  computeTree(menu.items, [...treeOperations])
                )}
                onChange={handleChange}
                onItemAdd={onItemAdd}
                onItemClick={onItemClick}
                onUndo={() =>
                  setTreeOperations(
                    treeOperations.slice(0, treeOperations.length - 1)
                  )
                }
              />
            </div>
          </Grid>
          <SaveButtonBar
            disabled={disabled || (!hasChanged && treeOperations.length === 0)}
            onCancel={onBack}
            onDelete={onDelete}
            onSave={submit}
            state={saveButtonState}
          />
        </Container>
      )}
    </Form>
  );
};
MenuDetailsPage.displayName = "MenuDetailsPage";
export default MenuDetailsPage;
