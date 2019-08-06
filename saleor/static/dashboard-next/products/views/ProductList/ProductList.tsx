import Button from "@material-ui/core/Button";
import DialogContentText from "@material-ui/core/DialogContentText";
import IconButton from "@material-ui/core/IconButton";
import DeleteIcon from "@material-ui/icons/Delete";
import React from "react";

import ActionDialog from "@saleor/components/ActionDialog";
import DeleteFilterTabDialog from "@saleor/components/DeleteFilterTabDialog";
import SaveFilterTabDialog, {
  SaveFilterTabDialogFormData
} from "@saleor/components/SaveFilterTabDialog";
import { defaultListSettings, ProductListColumns } from "@saleor/config";
import useBulkActions from "@saleor/hooks/useBulkActions";
import useListSettings from "@saleor/hooks/useListSettings";
import useLocale from "@saleor/hooks/useLocale";
import useNavigator from "@saleor/hooks/useNavigator";
import useNotifier from "@saleor/hooks/useNotifier";
import usePaginator, {
  createPaginationState
} from "@saleor/hooks/usePaginator";
import useShop from "@saleor/hooks/useShop";
import i18n from "@saleor/i18n";
import { getMutationState, maybe } from "@saleor/misc";
import { ListViews } from "@saleor/types";
import ProductListPage from "../../components/ProductListPage";
import {
  TypedProductBulkDeleteMutation,
  TypedProductBulkPublishMutation
} from "../../mutations";
import { TypedProductListQuery } from "../../queries";
import { productBulkDelete } from "../../types/productBulkDelete";
import { productBulkPublish } from "../../types/productBulkPublish";
import {
  productAddUrl,
  productListUrl,
  ProductListUrlDialog,
  ProductListUrlFilters,
  ProductListUrlQueryParams,
  productUrl
} from "../../urls";
import {
  areFiltersApplied,
  createFilter,
  createFilterChips,
  deleteFilterTab,
  getActiveFilters,
  getFilterTabs,
  getFilterVariables,
  saveFilterTab
} from "./filters";

interface ProductListProps {
  params: ProductListUrlQueryParams;
}

export const ProductList: React.StatelessComponent<ProductListProps> = ({
  params
}) => {
  const locale = useLocale();
  const navigate = useNavigator();
  const notify = useNotifier();
  const paginate = usePaginator();
  const shop = useShop();
  const { isSelected, listElements, reset, toggle, toggleAll } = useBulkActions(
    params.ids
  );
  const { updateListSettings, settings } = useListSettings<ProductListColumns>(
    ListViews.PRODUCT_LIST
  );
  const tabs = getFilterTabs();

  const currentTab =
    params.activeTab === undefined
      ? areFiltersApplied(params)
        ? tabs.length + 1
        : 0
      : parseInt(params.activeTab, 0);

  const closeModal = () =>
    navigate(
      productListUrl({
        ...params,
        action: undefined,
        ids: undefined
      }),
      true
    );

  const changeFilters = (filters: ProductListUrlFilters) => {
    reset();
    navigate(productListUrl(filters));
  };

  const changeFilterField = (filter: ProductListUrlFilters) => {
    reset();
    navigate(
      productListUrl({
        ...getActiveFilters(params),
        ...filter,
        activeTab: undefined
      })
    );
  };

  const openModal = (action: ProductListUrlDialog, ids?: string[]) =>
    navigate(
      productListUrl({
        ...params,
        action,
        ids
      })
    );

  const handleTabChange = (tab: number) => {
    reset();
    navigate(
      productListUrl({
        activeTab: tab.toString(),
        ...getFilterTabs()[tab - 1].data
      })
    );
  };

  const handleFilterTabDelete = () => {
    deleteFilterTab(currentTab);
    reset();
    navigate(productListUrl());
  };

  const handleFilterTabSave = (data: SaveFilterTabDialogFormData) => {
    saveFilterTab(data.name, getActiveFilters(params));
    handleTabChange(tabs.length + 1);
  };

  const paginationState = createPaginationState(settings.rowNumber, params);
  const currencySymbol = maybe(() => shop.defaultCurrency, "USD");
  const queryVariables = React.useMemo(
    () => ({
      ...paginationState,
      filter: getFilterVariables(params)
    }),
    [params, settings.rowNumber]
  );

  return (
    <TypedProductListQuery displayLoader variables={queryVariables}>
      {({ data, loading, refetch }) => {
        const { loadNextPage, loadPreviousPage, pageInfo } = paginate(
          maybe(() => data.products.pageInfo),
          paginationState,
          params
        );

        const handleBulkDelete = (data: productBulkDelete) => {
          if (data.productBulkDelete.errors.length === 0) {
            closeModal();
            notify({
              text: i18n.t("Products removed")
            });
            reset();
            refetch();
          }
        };

        const handleBulkPublish = (data: productBulkPublish) => {
          if (data.productBulkPublish.errors.length === 0) {
            closeModal();
            notify({
              text: i18n.t("Changed publication status")
            });
            reset();
            refetch();
          }
        };

        return (
          <TypedProductBulkDeleteMutation onCompleted={handleBulkDelete}>
            {(productBulkDelete, productBulkDeleteOpts) => (
              <TypedProductBulkPublishMutation onCompleted={handleBulkPublish}>
                {(productBulkPublish, productBulkPublishOpts) => {
                  const bulkDeleteMutationState = getMutationState(
                    productBulkDeleteOpts.called,
                    productBulkDeleteOpts.loading,
                    maybe(
                      () => productBulkDeleteOpts.data.productBulkDelete.errors
                    )
                  );

                  const bulkPublishMutationState = getMutationState(
                    productBulkPublishOpts.called,
                    productBulkPublishOpts.loading,
                    maybe(
                      () =>
                        productBulkPublishOpts.data.productBulkPublish.errors
                    )
                  );

                  return (
                    <>
                      <ProductListPage
                        currencySymbol={currencySymbol}
                        currentTab={currentTab}
                        defaultSettings={
                          defaultListSettings[ListViews.PRODUCT_LIST]
                        }
                        settings={settings}
                        filtersList={createFilterChips(
                          params,
                          {
                            currencySymbol,
                            locale
                          },
                          changeFilterField
                        )}
                        onAdd={() => navigate(productAddUrl)}
                        disabled={loading}
                        products={maybe(() =>
                          data.products.edges.map(edge => edge.node)
                        )}
                        onNextPage={loadNextPage}
                        onPreviousPage={loadPreviousPage}
                        onUpdateListSettings={updateListSettings}
                        pageInfo={pageInfo}
                        onRowClick={id => () => navigate(productUrl(id))}
                        onAll={() =>
                          changeFilters({
                            status: undefined
                          })
                        }
                        toolbar={
                          <>
                            <Button
                              color="primary"
                              onClick={() =>
                                openModal("unpublish", listElements)
                              }
                            >
                              {i18n.t("Unpublish")}
                            </Button>
                            <Button
                              color="primary"
                              onClick={() => openModal("publish", listElements)}
                            >
                              {i18n.t("Publish")}
                            </Button>
                            <IconButton
                              color="primary"
                              onClick={() => openModal("delete", listElements)}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </>
                        }
                        isChecked={isSelected}
                        selected={listElements.length}
                        toggle={toggle}
                        toggleAll={toggleAll}
                        onSearchChange={query => changeFilterField({ query })}
                        onFilterAdd={filter =>
                          changeFilterField(createFilter(filter))
                        }
                        onFilterSave={() => openModal("save-search")}
                        onFilterDelete={() => openModal("delete-search")}
                        onTabChange={handleTabChange}
                        initialSearch={params.query || ""}
                        filterTabs={getFilterTabs()}
                      />
                      <ActionDialog
                        open={params.action === "delete"}
                        confirmButtonState={bulkDeleteMutationState}
                        onClose={closeModal}
                        onConfirm={() =>
                          productBulkDelete({
                            variables: { ids: params.ids }
                          })
                        }
                        title={i18n.t("Remove products")}
                        variant="delete"
                      >
                        <DialogContentText
                          dangerouslySetInnerHTML={{
                            __html: i18n.t(
                              "Are you sure you want to remove <strong>{{ number }}</strong> products?",
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
                      <ActionDialog
                        open={params.action === "publish"}
                        confirmButtonState={bulkPublishMutationState}
                        onClose={closeModal}
                        onConfirm={() =>
                          productBulkPublish({
                            variables: {
                              ids: params.ids,
                              isPublished: true
                            }
                          })
                        }
                        title={i18n.t("Publish products")}
                      >
                        <DialogContentText
                          dangerouslySetInnerHTML={{
                            __html: i18n.t(
                              "Are you sure you want to publish <strong>{{ number }}</strong> products?",
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
                      <ActionDialog
                        open={params.action === "unpublish"}
                        confirmButtonState={bulkPublishMutationState}
                        onClose={closeModal}
                        onConfirm={() =>
                          productBulkPublish({
                            variables: {
                              ids: params.ids,
                              isPublished: false
                            }
                          })
                        }
                        title={i18n.t("Unpublish products")}
                      >
                        <DialogContentText
                          dangerouslySetInnerHTML={{
                            __html: i18n.t(
                              "Are you sure you want to unpublish <strong>{{ number }}</strong> products?",
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
                      <SaveFilterTabDialog
                        open={params.action === "save-search"}
                        confirmButtonState="default"
                        onClose={closeModal}
                        onSubmit={handleFilterTabSave}
                      />
                      <DeleteFilterTabDialog
                        open={params.action === "delete-search"}
                        confirmButtonState="default"
                        onClose={closeModal}
                        onSubmit={handleFilterTabDelete}
                        tabName={maybe(() => tabs[currentTab - 1].name, "...")}
                      />
                    </>
                  );
                }}
              </TypedProductBulkPublishMutation>
            )}
          </TypedProductBulkDeleteMutation>
        );
      }}
    </TypedProductListQuery>
  );
};
export default ProductList;
