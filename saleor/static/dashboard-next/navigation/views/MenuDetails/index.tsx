import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";

import { categoryUrl } from "../../../categories/urls";
import { collectionUrl } from "../../../collections/urls";
import ActionDialog from "../../../components/ActionDialog";
import { SearchPagesProvider } from "../../../containers/SearchPages";
import useNavigator from "../../../hooks/useNavigator";
import useNotifier from "../../../hooks/useNotifier";
import i18n from "../../../i18n";
import { getMutationState, maybe } from "../../../misc";
import { pageUrl } from "../../../pages/urls";
import { CategorySearchProvider } from "../../../products/containers/CategorySearch";
import { CollectionSearchProvider } from "../../../products/containers/CollectionSearch";
import MenuDetailsPage, {
  MenuDetailsSubmitData
} from "../../components/MenuDetailsPage";
import { findNode, getNode } from "../../components/MenuDetailsPage/tree";
import MenuItemDialog, {
  MenuItemDialogFormData,
  MenuItemType
} from "../../components/MenuItemDialog";
import {
  getItemId,
  getItemType,
  unknownTypeError
} from "../../components/MenuItems";
import {
  MenuDeleteMutation,
  MenuItemCreateMutation,
  MenuItemUpdateMutation,
  MenuUpdateMutation
} from "../../mutations";
import { MenuDetailsQuery } from "../../queries";
import { MenuItemCreateVariables } from "../../types/MenuItemCreate";
import { MenuItemUpdateVariables } from "../../types/MenuItemUpdate";
import { menuListUrl, menuUrl, MenuUrlQueryParams } from "../../urls";
import {
  handleDelete,
  handleItemCreate,
  handleItemUpdate,
  handleUpdate
} from "./successHandlers";
import {
  getInitialDisplayValue,
  getMenuItemInputData,
  getMoves,
  getRemoveIds
} from "./utils";

interface MenuDetailsProps {
  id: string;
  params: MenuUrlQueryParams;
}

const MenuDetails: React.FC<MenuDetailsProps> = ({ id, params }) => {
  const navigate = useNavigator();
  const notify = useNotifier();

  const closeModal = () =>
    navigate(
      menuUrl(id, {
        ...params,
        action: undefined,
        id: undefined
      }),
      true
    );

  const handleItemClick = (id: string, type: MenuItemType) => {
    switch (type) {
      case "category":
        navigate(categoryUrl(id));
        break;

      case "collection":
        navigate(collectionUrl(id));
        break;

      case "page":
        navigate(pageUrl(id));
        break;

      case "link":
        window.open(id, "blank");
        break;

      default:
        throw unknownTypeError;
        break;
    }
  };

  return (
    <SearchPagesProvider>
      {pageSearch => (
        <CategorySearchProvider>
          {categorySearch => (
            <CollectionSearchProvider>
              {collectionSearch => (
                <MenuDetailsQuery displayLoader variables={{ id }}>
                  {({ data, loading, refetch }) => {
                    const handleQueryChange = (query: string) => {
                      categorySearch.search(query);
                      collectionSearch.search(query);
                    };

                    const categories = maybe(
                      () =>
                        categorySearch.searchOpts.data.categories.edges.map(
                          edge => edge.node
                        ),
                      []
                    );

                    const collections = maybe(
                      () =>
                        collectionSearch.searchOpts.data.collections.edges.map(
                          edge => edge.node
                        ),
                      []
                    );

                    const pages = maybe(
                      () =>
                        pageSearch.searchOpts.data.pages.edges.map(
                          edge => edge.node
                        ),
                      []
                    );

                    return (
                      <MenuDeleteMutation
                        onCompleted={data =>
                          handleDelete(data, navigate, notify)
                        }
                      >
                        {(menuDelete, menuDeleteOpts) => (
                          <MenuUpdateMutation
                            onCompleted={data =>
                              handleUpdate(data, notify, refetch)
                            }
                          >
                            {(menuUpdate, menuUpdateOpts) => {
                              const deleteState = getMutationState(
                                menuDeleteOpts.called,
                                menuDeleteOpts.loading,
                                maybe(
                                  () => menuDeleteOpts.data.menuDelete.errors
                                )
                              );

                              const updateState = getMutationState(
                                menuUpdateOpts.called,
                                menuUpdateOpts.loading,
                                maybe(
                                  () => menuUpdateOpts.data.menuUpdate.errors
                                ),
                                maybe(
                                  () => menuUpdateOpts.data.menuItemMove.errors
                                )
                              );

                              // This is a workaround to let know <MenuDetailsPage />
                              // that it should clean operation stack if mutations
                              // were successful
                              const handleSubmit = async (
                                data: MenuDetailsSubmitData
                              ) => {
                                try {
                                  const result = await menuUpdate({
                                    variables: {
                                      id,
                                      moves: getMoves(data),
                                      name: data.name,
                                      removeIds: getRemoveIds(data)
                                    }
                                  });
                                  if (result) {
                                    if (
                                      result.data.menuItemBulkDelete.errors
                                        .length > 0 ||
                                      result.data.menuItemMove.errors.length >
                                        0 ||
                                      result.data.menuUpdate.errors.length > 0
                                    ) {
                                      return false;
                                    }
                                  }
                                  return true;
                                } catch {
                                  return false;
                                }
                              };

                              return (
                                <>
                                  <MenuDetailsPage
                                    disabled={loading}
                                    menu={maybe(() => data.menu)}
                                    onBack={() => navigate(menuListUrl())}
                                    onDelete={() =>
                                      navigate(
                                        menuUrl(id, {
                                          action: "remove"
                                        })
                                      )
                                    }
                                    onItemAdd={() =>
                                      navigate(
                                        menuUrl(id, {
                                          action: "add-item"
                                        })
                                      )
                                    }
                                    onItemClick={handleItemClick}
                                    onItemEdit={itemId =>
                                      navigate(
                                        menuUrl(id, {
                                          action: "edit-item",
                                          id: itemId
                                        })
                                      )
                                    }
                                    onSubmit={handleSubmit}
                                    saveButtonState={updateState}
                                  />
                                  <ActionDialog
                                    open={params.action === "remove"}
                                    onClose={closeModal}
                                    confirmButtonState={deleteState}
                                    onConfirm={() =>
                                      menuDelete({ variables: { id } })
                                    }
                                    variant="delete"
                                    title={i18n.t("Remove menu")}
                                  >
                                    <DialogContentText
                                      dangerouslySetInnerHTML={{
                                        __html: i18n.t(
                                          "Are you sure you want to remove menu <strong>{{ name }}</strong>?",
                                          {
                                            name: maybe(
                                              () => data.menu.name,
                                              "..."
                                            )
                                          }
                                        )
                                      }}
                                    />
                                  </ActionDialog>

                                  <MenuItemCreateMutation
                                    onCompleted={data =>
                                      handleItemCreate(data, notify, closeModal)
                                    }
                                  >
                                    {(menuItemCreate, menuItemCreateOpts) => {
                                      const handleSubmit = (
                                        data: MenuItemDialogFormData
                                      ) => {
                                        const variables: MenuItemCreateVariables = {
                                          input: {
                                            menu: id,
                                            ...getMenuItemInputData(data)
                                          }
                                        };

                                        menuItemCreate({ variables });
                                      };

                                      const formTransitionState = getMutationState(
                                        menuItemCreateOpts.called,
                                        menuItemCreateOpts.loading,
                                        maybe(
                                          () =>
                                            menuItemCreateOpts.data
                                              .menuItemCreate.errors
                                        )
                                      );

                                      return (
                                        <MenuItemDialog
                                          open={params.action === "add-item"}
                                          categories={categories}
                                          collections={collections}
                                          pages={pages}
                                          loading={
                                            categorySearch.searchOpts.loading ||
                                            collectionSearch.searchOpts.loading
                                          }
                                          confirmButtonState={
                                            formTransitionState
                                          }
                                          disabled={menuItemCreateOpts.loading}
                                          onClose={closeModal}
                                          onSubmit={handleSubmit}
                                          onQueryChange={handleQueryChange}
                                        />
                                      );
                                    }}
                                  </MenuItemCreateMutation>
                                  <MenuItemUpdateMutation
                                    onCompleted={data =>
                                      handleItemUpdate(
                                        data,
                                        id,
                                        navigate,
                                        notify
                                      )
                                    }
                                  >
                                    {(menuItemUpdate, menuItemUpdateOpts) => {
                                      const handleSubmit = (
                                        data: MenuItemDialogFormData
                                      ) => {
                                        const variables: MenuItemUpdateVariables = {
                                          id: params.id,
                                          input: getMenuItemInputData(data)
                                        };

                                        menuItemUpdate({ variables });
                                      };

                                      const menuItem = maybe(() =>
                                        getNode(
                                          data.menu.items,
                                          findNode(data.menu.items, params.id)
                                        )
                                      );

                                      const formTransitionState = getMutationState(
                                        menuItemUpdateOpts.called,
                                        menuItemUpdateOpts.loading,
                                        maybe(
                                          () =>
                                            menuItemUpdateOpts.data
                                              .menuItemUpdate.errors
                                        )
                                      );

                                      const initialFormData: MenuItemDialogFormData = {
                                        id: maybe(() => getItemId(menuItem)),
                                        name: maybe(() => menuItem.name, "..."),
                                        type: maybe<MenuItemType>(
                                          () => getItemType(menuItem),
                                          "category"
                                        )
                                      };

                                      return (
                                        <MenuItemDialog
                                          open={params.action === "edit-item"}
                                          categories={categories}
                                          collections={collections}
                                          pages={pages}
                                          initial={initialFormData}
                                          initialDisplayValue={getInitialDisplayValue(
                                            menuItem
                                          )}
                                          loading={
                                            categorySearch.searchOpts.loading ||
                                            collectionSearch.searchOpts.loading
                                          }
                                          confirmButtonState={
                                            formTransitionState
                                          }
                                          disabled={menuItemUpdateOpts.loading}
                                          onClose={closeModal}
                                          onSubmit={handleSubmit}
                                          onQueryChange={handleQueryChange}
                                        />
                                      );
                                    }}
                                  </MenuItemUpdateMutation>
                                </>
                              );
                            }}
                          </MenuUpdateMutation>
                        )}
                      </MenuDeleteMutation>
                    );
                  }}
                </MenuDetailsQuery>
              )}
            </CollectionSearchProvider>
          )}
        </CategorySearchProvider>
      )}
    </SearchPagesProvider>
  );
};
MenuDetails.displayName = "MenuDetails";

export default MenuDetails;
