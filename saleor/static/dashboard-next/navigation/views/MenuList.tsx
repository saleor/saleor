import Button from "@material-ui/core/Button";
import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";

import ActionDialog from "../../components/ActionDialog";
import { createPaginationState } from "../../components/Paginator";
import { configurationMenuUrl } from "../../configuration";
import useBulkActions from "../../hooks/useBulkActions";
import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import usePaginator from "../../hooks/usePaginator";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import MenuCreateDialog from "../components/MenuCreateDialog";
import MenuListPage from "../components/MenuListPage";
import {
  MenuBulkDeleteMutation,
  MenuCreateMutation,
  MenuDeleteMutation
} from "../mutations";
import { MenuListQuery } from "../queries";
import { MenuBulkDelete } from "../types/MenuBulkDelete";
import { MenuCreate } from "../types/MenuCreate";
import { MenuDelete } from "../types/MenuDelete";
import { menuListUrl, MenuListUrlQueryParams, menuUrl } from "../urls";

const PAGINATE_BY = 20;

interface MenuListProps {
  params: MenuListUrlQueryParams;
}
const MenuList: React.FC<MenuListProps> = ({ params }) => {
  const navigate = useNavigator();
  const notify = useNotifier();
  const paginate = usePaginator();
  const { isSelected, listElements, reset, toggle } = useBulkActions(
    params.ids
  );

  const closeModal = () =>
    navigate(
      menuListUrl({
        ...params,
        action: undefined,
        id: undefined,
        ids: undefined
      }),
      true
    );

  const paginationState = createPaginationState(PAGINATE_BY, params);

  return (
    <MenuListQuery variables={paginationState}>
      {({ data, loading, refetch }) => {
        const { loadNextPage, loadPreviousPage, pageInfo } = paginate(
          maybe(() => data.menus.pageInfo),
          paginationState,
          params
        );

        const handleCreate = (data: MenuCreate) => {
          if (data.menuCreate.errors.length === 0) {
            notify({
              text: i18n.t("Created menu", {
                context: "notification"
              })
            });
            navigate(menuUrl(data.menuCreate.menu.id));
          }
        };

        const handleBulkDelete = (data: MenuBulkDelete) => {
          if (data.menuBulkDelete.errors.length === 0) {
            notify({
              text: i18n.t("Removed menus", {
                context: "notification"
              })
            });
            closeModal();
            reset();
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
            closeModal();
            refetch();
          }
        };

        return (
          <MenuCreateMutation onCompleted={handleCreate}>
            {(menuCreate, menuCreateOpts) => (
              <MenuDeleteMutation onCompleted={handleDelete}>
                {(menuDelete, menuDeleteOpts) => (
                  <MenuBulkDeleteMutation onCompleted={handleBulkDelete}>
                    {(menuBulkDelete, menuBulkDeleteOpts) => {
                      const createTransitionState = getMutationState(
                        menuCreateOpts.called,
                        menuCreateOpts.loading,
                        maybe(() => menuCreateOpts.data.menuCreate.errors)
                      );

                      const deleteTransitionState = getMutationState(
                        menuDeleteOpts.called,
                        menuDeleteOpts.loading,
                        maybe(() => menuDeleteOpts.data.menuDelete.errors)
                      );

                      const bulkDeleteTransitionState = getMutationState(
                        menuBulkDeleteOpts.called,
                        menuBulkDeleteOpts.loading,
                        maybe(
                          () => menuBulkDeleteOpts.data.menuBulkDelete.errors
                        )
                      );

                      return (
                        <>
                          <MenuListPage
                            disabled={loading}
                            menus={maybe(() =>
                              data.menus.edges.map(edge => edge.node)
                            )}
                            onAdd={() =>
                              navigate(
                                menuListUrl({
                                  action: "add"
                                })
                              )
                            }
                            onBack={() => navigate(configurationMenuUrl)}
                            onDelete={id =>
                              navigate(
                                menuListUrl({
                                  action: "remove",
                                  id
                                })
                              )
                            }
                            onNextPage={loadNextPage}
                            onPreviousPage={loadPreviousPage}
                            onRowClick={id => () => navigate(menuUrl(id))}
                            pageInfo={pageInfo}
                            isChecked={isSelected}
                            selected={listElements.length}
                            toggle={toggle}
                            toolbar={
                              <Button
                                color="primary"
                                onClick={() =>
                                  navigate(
                                    menuListUrl({
                                      ...params,
                                      action: "remove-many",
                                      ids: listElements
                                    })
                                  )
                                }
                              >
                                {i18n.t("Remove")}
                              </Button>
                            }
                          />
                          <MenuCreateDialog
                            open={params.action === "add"}
                            confirmButtonState={createTransitionState}
                            disabled={menuCreateOpts.loading}
                            onClose={closeModal}
                            onConfirm={formData =>
                              menuCreate({
                                variables: { input: formData }
                              })
                            }
                          />
                          <ActionDialog
                            open={params.action === "remove"}
                            onClose={closeModal}
                            confirmButtonState={deleteTransitionState}
                            onConfirm={() =>
                              menuDelete({
                                variables: {
                                  id: params.id
                                }
                              })
                            }
                            variant="delete"
                            title={i18n.t("Remove menu")}
                          >
                            <DialogContentText
                              dangerouslySetInnerHTML={{
                                __html: i18n.t(
                                  "Are you sure you want to remove <strong>{{ name }}</strong>?",
                                  {
                                    name: maybe(
                                      () =>
                                        data.menus.edges.find(
                                          edge => edge.node.id === params.id
                                        ).node.name,
                                      "..."
                                    )
                                  }
                                )
                              }}
                            />
                          </ActionDialog>
                          <ActionDialog
                            open={params.action === "remove-many"}
                            onClose={closeModal}
                            confirmButtonState={bulkDeleteTransitionState}
                            onConfirm={() =>
                              menuBulkDelete({
                                variables: {
                                  ids: params.ids
                                }
                              })
                            }
                            variant="delete"
                            title={i18n.t("Remove menus")}
                          >
                            <DialogContentText
                              dangerouslySetInnerHTML={{
                                __html: i18n.t(
                                  "Are you sure you want to remove <strong>{{ number }}</strong> menus?",
                                  {
                                    number: maybe(
                                      () => params.ids.length.toString(),
                                      "..."
                                    )
                                  }
                                )
                              }}
                            />
                          </ActionDialog>
                        </>
                      );
                    }}
                  </MenuBulkDeleteMutation>
                )}
              </MenuDeleteMutation>
            )}
          </MenuCreateMutation>
        );
      }}
    </MenuListQuery>
  );
};
export default MenuList;
