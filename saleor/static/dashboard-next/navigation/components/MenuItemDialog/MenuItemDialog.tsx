import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import TextField from "@material-ui/core/TextField";
import isUrl from "is-url";
import React from "react";

import AutocompleteSelectMenu from "@saleor/components/AutocompleteSelectMenu";
import ConfirmButton, {
  ConfirmButtonTransitionState
} from "@saleor/components/ConfirmButton";
import FormSpacer from "@saleor/components/FormSpacer";
import { SearchCategories_categories_edges_node } from "../../../containers/SearchCategories/types/SearchCategories";
import { SearchCollections_collections_edges_node } from "../../../containers/SearchCollections/types/SearchCollections";
import { SearchPages_pages_edges_node } from "../../../containers/SearchPages/types/SearchPages";
import i18n from "../../../i18n";
import { getMenuItemByValue, IMenu } from "../../../utils/menu";

export type MenuItemType = "category" | "collection" | "link" | "page";
export interface MenuItemData {
  id: string;
  type: MenuItemType;
}

export interface MenuItemDialogFormData extends MenuItemData {
  name: string;
}

export interface MenuItemDialogProps {
  confirmButtonState: ConfirmButtonTransitionState;
  disabled: boolean;
  initial?: MenuItemDialogFormData;
  initialDisplayValue?: string;
  loading: boolean;
  open: boolean;
  collections: SearchCollections_collections_edges_node[];
  categories: SearchCategories_categories_edges_node[];
  pages: SearchPages_pages_edges_node[];
  onClose: () => void;
  onSubmit: (data: MenuItemDialogFormData) => void;
  onQueryChange: (query: string) => void;
}

const defaultInitial: MenuItemDialogFormData = {
  id: "",
  name: "",
  type: "category"
};

function getMenuItemData(value: string): MenuItemData {
  const [type, ...idParts] = value.split(":");
  return {
    id: idParts.join(":"),
    type: type as MenuItemType
  };
}

function getDisplayValue(menu: IMenu, value: string): string {
  const menuItemData = getMenuItemData(value);
  if (menuItemData.type === "link") {
    return menuItemData.id;
  }
  return getMenuItemByValue(menu, value).label.toString();
}

const MenuItemDialog: React.StatelessComponent<MenuItemDialogProps> = ({
  confirmButtonState,
  disabled,
  initial,
  initialDisplayValue,
  loading,
  onClose,
  onSubmit,
  onQueryChange,
  open,
  categories,
  collections,
  pages
}) => {
  const [displayValue, setDisplayValue] = React.useState(
    initialDisplayValue || ""
  );
  const [data, setData] = React.useState<MenuItemDialogFormData>(
    initial || defaultInitial
  );
  const [url, setUrl] = React.useState<string>(undefined);

  // Refresh initial display value if changed
  React.useEffect(() => setDisplayValue(initialDisplayValue), [
    initialDisplayValue
  ]);

  // Reset input state after closing dialog
  React.useEffect(() => {
    setDisplayValue(initialDisplayValue);
    setUrl(undefined);
  }, [open]);

  let options: IMenu = [];

  if (categories.length > 0) {
    options = [
      ...options,
      {
        children: categories.map(category => ({
          children: [],
          data: {},
          label: category.name,
          value: "category:" + category.id
        })),
        data: {},
        label: i18n.t("Categories")
      }
    ];
  }

  if (collections.length > 0) {
    options = [
      ...options,
      {
        children: collections.map(collection => ({
          children: [],
          data: {},
          label: collection.name,
          value: "collection:" + collection.id
        })),
        data: {},
        label: i18n.t("Collections")
      }
    ];
  }

  if (pages.length > 0) {
    options = [
      ...options,
      {
        children: pages.map(page => ({
          children: [],
          data: {},
          label: page.title,
          value: "page:" + page.id
        })),
        data: {},
        label: i18n.t("Pages")
      }
    ];
  }

  if (url) {
    options = [
      {
        children: [],
        data: {},
        label: (
          <div
            dangerouslySetInnerHTML={{
              __html: i18n.t("Link to: <strong>{{ url }}</strong>", {
                context: "add link to navigation",
                url
              })
            }}
          />
        ),
        value: "link:" + url
      }
    ];
  }

  const handleQueryChange = (query: string) => {
    if (isUrl(query)) {
      setUrl(query);
    } else if (isUrl("http://" + query)) {
      setUrl("http://" + query);
    } else if (url) {
      setUrl(undefined);
    }
    onQueryChange(query);
  };

  const handleSelectChange = (event: React.ChangeEvent<any>) => {
    const value = event.target.value;
    const menuItemData = getMenuItemData(value);

    setData(value => ({
      ...value,
      ...menuItemData
    }));
    setDisplayValue(getDisplayValue(options, value));
  };

  const handleSubmit = () => onSubmit(data);

  return (
    <Dialog
      onClose={onClose}
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
      <DialogContent style={{ overflowY: "visible" }}>
        <TextField
          disabled={disabled}
          label={i18n.t("Name")}
          fullWidth
          value={data.name}
          onChange={event =>
            setData(value => ({
              ...value,
              name: event.target.value
            }))
          }
          name="name"
          helperText=""
        />
        <FormSpacer />
        <AutocompleteSelectMenu
          disabled={disabled}
          onChange={handleSelectChange}
          name="id"
          helperText=""
          label={i18n.t("Link")}
          displayValue={displayValue}
          loading={loading}
          error={false}
          options={options}
          placeholder={i18n.t("Start typing to begin search...")}
          onInputChange={handleQueryChange}
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
          onClick={handleSubmit}
        >
          {i18n.t("Submit", { context: "button" })}
        </ConfirmButton>
      </DialogActions>
    </Dialog>
  );
};
MenuItemDialog.displayName = "MenuItemDialog";
export default MenuItemDialog;
