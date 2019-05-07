import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import AutocompleteSelectMenu, {
  SelectMenuItem
} from "../../../components/AutocompleteSelectMenu";
import ConfirmButton, {
  ConfirmButtonTransitionState
} from "../../../components/ConfirmButton";
import Form from "../../../components/Form";
import FormSpacer from "../../../components/FormSpacer";
import { SearchCategories_categories_edges_node } from "../../../containers/SearchCategories/types/SearchCategories";
import { SearchCollections_collections_edges_node } from "../../../containers/SearchCollections/types/SearchCollections";
import { SearchProducts_products_edges_node } from "../../../containers/SearchProducts/types/SearchProducts";
import i18n from "../../../i18n";

export type MenuItemType =
  | "category"
  | "collection"
  | "link"
  | "page"
  | "product";
export interface MenuItemData {
  id: string;
  type: MenuItemType;
}

export interface MenuCreateItemDialogFormData extends MenuItemData {
  name: string;
}

export interface MenuCreateItemDialogProps {
  confirmButtonState: ConfirmButtonTransitionState;
  disabled: boolean;
  initial?: MenuCreateItemDialogFormData;
  loading: boolean;
  open: boolean;
  products: SearchProducts_products_edges_node[];
  collections: SearchCollections_collections_edges_node[];
  categories: SearchCategories_categories_edges_node[];
  onClose: () => void;
  onSubmit: (data: MenuCreateItemDialogFormData) => void;
  onQueryChange: (query: string) => void;
}

const defaultInitial: MenuCreateItemDialogFormData = {
  id: "",
  name: "",
  type: "category"
};

function findMenuItem(menu: SelectMenuItem[], value: string): SelectMenuItem {
  const matches = menu.map(menuItem =>
    menuItem.children
      ? findMenuItem(menuItem.children, value)
      : menuItem.value === value
      ? menuItem
      : null
  );
  return matches.find(match => match !== null);
}

function getMenuItemData(value: string): MenuItemData {
  const [type, ...idParts] = value.split(":");
  return {
    id: idParts.reduce((acc, part) => acc + part, ""),
    type: type as MenuItemType
  };
}

function getDisplayValue(menu: SelectMenuItem[], value: string): string {
  return findMenuItem(menu, value).label.toString();
}

const MenuCreateItemDialog: React.StatelessComponent<
  MenuCreateItemDialogProps
> = ({
  confirmButtonState,
  disabled,
  initial,
  loading,
  onClose,
  onSubmit,
  onQueryChange,
  open,
  categories,
  collections,
  products
}) => {
  const [displayValue, setDisplayValue] = React.useState("");

  const options: SelectMenuItem[] = [
    {
      children: categories.map(category => ({
        label: category.name,
        value: "category:" + category.id
      })),
      label: i18n.t("Categories ({{ number }})", {
        number: categories.length
      })
    },
    {
      children: collections.map(collection => ({
        label: collection.name,
        value: "collection:" + collection.id
      })),
      label: i18n.t("Collections ({{ number }})", {
        number: collections.length
      })
    },
    {
      children: products.map(product => ({
        label: product.name,
        value: "product:" + product.id
      })),
      label: i18n.t("Products ({{ number }})", {
        number: products.length
      })
    }
  ];

  return (
    <Dialog
      open={open}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        style: { overflowY: "visible" }
      }}
    >
      <DialogTitle>
        {i18n.t("Add Item", {
          context: "create new menu item"
        })}
      </DialogTitle>
      <Form initial={initial || defaultInitial} onSubmit={onSubmit}>
        {({ change, data, submit }) => {
          const handleSelectChange = (event: React.ChangeEvent<any>) => {
            const value = event.target.value;
            const menuItemData = getMenuItemData(value);
            change(
              {
                target: {
                  name: "id",
                  value: menuItemData.id
                }
              } as any,
              () =>
                change(
                  {
                    target: {
                      name: "type",
                      value: menuItemData.type
                    }
                  } as any,
                  () => setDisplayValue(getDisplayValue(options, value))
                )
            );
          };

          return (
            <>
              <DialogContent style={{ overflowY: "visible" }}>
                <TextField
                  disabled={disabled}
                  label={i18n.t("Name")}
                  fullWidth
                  value={data.name}
                  onChange={change}
                  name={"name" as keyof MenuCreateItemDialogFormData}
                  helperText=""
                />
                <FormSpacer />
                <AutocompleteSelectMenu
                  disabled={disabled}
                  onChange={handleSelectChange}
                  name={"id" as keyof MenuCreateItemDialogFormData}
                  helperText=""
                  label={i18n.t("Link")}
                  displayValue={displayValue}
                  loading={loading}
                  error={false}
                  options={options}
                  placeholder={i18n.t("Start typing to begin search...")}
                  onInputChange={onQueryChange}
                />
              </DialogContent>
              <DialogActions>
                <Button onClick={onClose}>
                  {i18n.t("Cancel", { context: "button" })}
                </Button>
                <ConfirmButton
                  transitionState={confirmButtonState}
                  color="primary"
                  variant="contained"
                  onClick={submit}
                >
                  {i18n.t("Submit", { context: "button" })}
                </ConfirmButton>
              </DialogActions>
            </>
          );
        }}
      </Form>
    </Dialog>
  );
};
MenuCreateItemDialog.displayName = "MenuCreateItemDialog";
export default MenuCreateItemDialog;
