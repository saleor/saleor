import Typography from "@material-ui/core/Typography";
import * as React from "react";

import AppHeader from "../../../components/AppHeader";
import CardSpacer from "../../../components/CardSpacer";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton";
import Container from "../../../components/Container";
import Grid from "../../../components/Grid";
import SaveButtonBar from "../../../components/SaveButtonBar";
import i18n from "../../../i18n";
import { MenuDetails_menu } from "../../types/MenuDetails";
import MenuProperties from "../MenuProperties";
import Form from "../../../components/Form";
import { maybe } from "../../../misc";

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

  return (
    <Form initial={initialForm}>
      {({ change, data, hasChanged, errors: FormErrors }) => (
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
            </div>
          </Grid>
          <SaveButtonBar
            disabled={disabled || !hasChanged}
            onCancel={onBack}
            onDelete={onDelete}
            onSave={onSubmit}
            state={saveButtonState}
          />
        </Container>
      )}
    </Form>
  );
};
MenuDetailsPage.displayName = "MenuDetailsPage";
export default MenuDetailsPage;
