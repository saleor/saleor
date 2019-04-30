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
import MenuItems, { TreePermutation } from "../MenuItems";
import MenuProperties from "../MenuProperties";
import { computeTree } from "./tree";

export interface MenuDetailsFormData {
  name: string;
}

export interface MenuDetailsPageProps {
  saveButtonState: ConfirmButtonTransitionState;
  disabled: boolean;
  menu: MenuDetails_menu;
  onBack: () => void;
  onDelete: () => void;
  onSubmit: () => void;
}

const MenuDetailsPage: React.StatelessComponent<MenuDetailsPageProps> = ({
  disabled,
  menu,
  saveButtonState,
  onBack,
  onDelete,
  onSubmit
}) => {
  const initialForm: MenuDetailsFormData = {
    name: maybe(() => menu.name)
  };

  const [treePermutations, setTreePermutations] = React.useState<
    TreePermutation[]
  >([]);

  const handleSubmit = () => {
    onSubmit();
  };

  return (
    <Form initial={initialForm}>
      {({ change, data, hasChanged }) => (
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
                items={computeTree(maybe(() => menu.items), treePermutations)}
                onChange={permutation =>
                  !!permutation
                    ? setTreePermutations([...treePermutations, permutation])
                    : undefined
                }
              />
            </div>
          </Grid>
          <SaveButtonBar
            disabled={disabled || !hasChanged}
            onCancel={onBack}
            onDelete={onDelete}
            onSave={handleSubmit}
            state={saveButtonState}
          />
        </Container>
      )}
    </Form>
  );
};
MenuDetailsPage.displayName = "MenuDetailsPage";
export default MenuDetailsPage;
