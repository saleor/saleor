import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";

import ActionDialog from "../../components/ActionDialog";
import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import { CategorySearchProvider } from "../../products/containers/CategorySearch";
import { CollectionSearchProvider } from "../../products/containers/CollectionSearch";
import MenuCreateItemDialog, {
  MenuCreateItemDialogFormData
} from "../components/MenuCreateItemDialog";
import MenuDetailsPage, {
  MenuDetailsSubmitData
} from "../components/MenuDetailsPage";
import {
  MenuDeleteMutation,
  MenuItemCreateMutation,
  MenuUpdateMutation
} from "../mutations";
import { MenuDetailsQuery } from "../queries";
import { MenuDelete } from "../types/MenuDelete";
import {
  MenuItemCreate,
  MenuItemCreateVariables
} from "../types/MenuItemCreate";
import { MenuUpdate } from "../types/MenuUpdate";
import { menuListUrl, menuUrl, MenuUrlQueryParams } from "../urls";

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

  const handleItemCreate = (data: MenuItemCreate) => {
    if (data.menuItemCreate.errors.length === 0) {
      closeModal();
      notify({
        text: i18n.t("Created menu item", {
          context: "notification"
        })
      });
    }
  };

  return (
    <MenuDetailsQuery displayLoader variables={{ id }}>
      {({ data, loading, refetch }) => {
        const handleUpdate = (data: MenuUpdate) => {
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
        };

        const handleDelete = (data: MenuDelete) => {
          if (data.menuDelete.errors.length === 0) {
            notify({
              text: i18n.t("Removed menu", {
                context: "notification"
              })
            });
            navigate(menuListUrl(), true);
          }
        };

        return (
          <MenuDeleteMutation onCompleted={handleDelete}>
            {(menuDelete, menuDeleteOpts) => (
              <MenuUpdateMutation onCompleted={handleUpdate}>
                {(menuUpdate, menuUpdateOpts) => {
                  const deleteState = getMutationState(
                    menuDeleteOpts.called,
                    menuDeleteOpts.loading,
                    maybe(() => menuDeleteOpts.data.menuDelete.errors)
                  );

                  const updateState = getMutationState(
                    menuUpdateOpts.called,
                    menuUpdateOpts.loading,
                    maybe(() => menuUpdateOpts.data.menuUpdate.errors),
                    maybe(() => menuUpdateOpts.data.menuItemMove.errors)
                  );

                  const handleSubmit = async (data: MenuDetailsSubmitData) => {
                    try {
                      const result = await menuUpdate({
                        variables: {
                          id,
                          moves: data.operations
                            .filter(operation => operation.type === "move")
                            .map(move => ({
                              itemId: move.id,
                              parentId: move.parentId,
                              sortOrder: move.sortOrder
                            })),
                          name: data.name,
                          removeIds: data.operations
                            .filter(operation => operation.type === "remove")
                            .map(operation => operation.id)
                        }
                      });
                      if (result) {
                        if (
                          result.data.menuItemBulkDelete.errors.length > 0 ||
                          result.data.menuItemMove.errors.length > 0 ||
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
                        onSubmit={handleSubmit}
                        saveButtonState={updateState}
                      />
                      <ActionDialog
                        open={params.action === "remove"}
                        onClose={closeModal}
                        confirmButtonState={deleteState}
                        onConfirm={() => menuDelete({ variables: { id } })}
                        variant="delete"
                        title={i18n.t("Remove menu")}
                      >
                        <DialogContentText
                          dangerouslySetInnerHTML={{
                            __html: i18n.t(
                              "Are you sure you want to remove menu <strong>{{ name }}</strong>?",
                              {
                                name: maybe(() => data.menu.name, "...")
                              }
                            )
                          }}
                        />
                      </ActionDialog>

                      <MenuItemCreateMutation onCompleted={handleItemCreate}>
                        {(menuItemCreate, menuItemCreateOpts) => {
                          const handleSubmit = (
                            data: MenuCreateItemDialogFormData
                          ) => {
                            const variables: MenuItemCreateVariables = {
                              input: {
                                menu: id,
                                name: data.name
                              }
                            };
                            switch (data.type) {
                              case "category":
                                variables.input.category = data.id;
                                break;

                              case "collection":
                                variables.input.collection = data.id;
                                break;

                              case "link":
                                variables.input.url = data.id;
                                break;

                              default:
                                throw new Error("Unknown type");
                                break;
                            }
                            menuItemCreate({ variables });
                          };

                          const formTransitionState = getMutationState(
                            menuItemCreateOpts.called,
                            menuItemCreateOpts.loading,
                            maybe(
                              () =>
                                menuItemCreateOpts.data.menuItemCreate.errors
                            )
                          );

                          return (
                            <CategorySearchProvider>
                              {categorySearch => (
                                <CollectionSearchProvider>
                                  {collectionSearch => {
                                    const handleQueryChange = (
                                      query: string
                                    ) => {
                                      categorySearch.search(query);
                                      collectionSearch.search(query);
                                    };

                                    return (
                                      <MenuCreateItemDialog
                                        open={params.action === "add-item"}
                                        categories={maybe(
                                          () =>
                                            categorySearch.searchOpts.data.categories.edges.map(
                                              edge => edge.node
                                            ),
                                          []
                                        )}
                                        collections={maybe(
                                          () =>
                                            collectionSearch.searchOpts.data.collections.edges.map(
                                              edge => edge.node
                                            ),
                                          []
                                        )}
                                        loading={
                                          categorySearch.searchOpts.loading ||
                                          collectionSearch.searchOpts.loading
                                        }
                                        confirmButtonState={formTransitionState}
                                        disabled={menuItemCreateOpts.loading}
                                        onClose={closeModal}
                                        onSubmit={handleSubmit}
                                        onQueryChange={handleQueryChange}
                                      />
                                    );
                                  }}
                                </CollectionSearchProvider>
                              )}
                            </CategorySearchProvider>
                          );
                        }}
                      </MenuItemCreateMutation>
                    </>
                  );
                }}
              </MenuUpdateMutation>
            )}
          </MenuDeleteMutation>
        );
      }}
    </MenuDetailsQuery>
  );
};
MenuDetails.displayName = "MenuDetails";

export default MenuDetails;
