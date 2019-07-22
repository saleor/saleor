import { UseNavigatorResult } from "../../../hooks/useNavigator";
import { UseNotifierResult } from "../../../hooks/useNotifier";
import i18n from "../../../i18n";
import { MenuDelete } from "../../types/MenuDelete";
import { MenuItemCreate } from "../../types/MenuItemCreate";
import { MenuItemUpdate } from "../../types/MenuItemUpdate";
import { MenuUpdate } from "../../types/MenuUpdate";
import { menuListUrl, menuUrl } from "../../urls";

export function handleItemCreate(
  data: MenuItemCreate,
  notify: UseNotifierResult,
  closeModal: () => void
) {
  if (data.menuItemCreate.errors.length === 0) {
    closeModal();
    notify({
      text: i18n.t("Created menu item", {
        context: "notification"
      })
    });
  }
}

export function handleItemUpdate(
  data: MenuItemUpdate,
  id: string,
  navigate: UseNavigatorResult,
  notify: UseNotifierResult
) {
  if (data.menuItemUpdate.errors.length === 0) {
    notify({
      text: i18n.t("Updated menu item", {
        context: "notification"
      })
    });
    navigate(
      menuUrl(id, {
        action: undefined,
        id: undefined
      })
    );
  }
}

export function handleDelete(
  data: MenuDelete,
  navigate: UseNavigatorResult,
  notify: UseNotifierResult
) {
  if (data.menuDelete.errors.length === 0) {
    notify({
      text: i18n.t("Removed menu", {
        context: "notification"
      })
    });
    navigate(menuListUrl(), true);
  }
}

export function handleUpdate(
  data: MenuUpdate,
  notify: UseNotifierResult,
  refetch: () => void
) {
  if (
    data.menuItemBulkDelete.errors.length === 0 &&
    data.menuItemMove.errors.length === 0 &&
    data.menuUpdate.errors.length === 0
  ) {
    notify({
      text: i18n.t("Updated menu", {
        context: "notification"
      })
    });
    refetch();
  }
}
