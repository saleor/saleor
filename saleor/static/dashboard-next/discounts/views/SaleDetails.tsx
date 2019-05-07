import Button from "@material-ui/core/Button";
import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";

import { categoryUrl } from "../../categories/urls";
import { collectionUrl } from "../../collections/urls";
import ActionDialog from "../../components/ActionDialog";
import AssignCategoriesDialog from "../../components/AssignCategoryDialog";
import AssignCollectionDialog from "../../components/AssignCollectionDialog";
import AssignProductDialog from "../../components/AssignProductDialog";
import { createPaginationState } from "../../components/Paginator";
import { WindowTitle } from "../../components/WindowTitle";
import { SearchCategoriesProvider } from "../../containers/SearchCategories";
import { SearchCollectionsProvider } from "../../containers/SearchCollections";
import { SearchProductsProvider } from "../../containers/SearchProducts";
import useBulkActions from "../../hooks/useBulkActions";
import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import usePaginator from "../../hooks/usePaginator";
import useShop from "../../hooks/useShop";
import i18n from "../../i18n";
import { decimal, getMutationState, maybe } from "../../misc";
import { productUrl } from "../../products/urls";
import { DiscountValueTypeEnum, SaleType } from "../../types/globalTypes";
import SaleDetailsPage, {
  SaleDetailsPageTab
} from "../components/SaleDetailsPage";
import {
  TypedSaleCataloguesAdd,
  TypedSaleCataloguesRemove,
  TypedSaleDelete,
  TypedSaleUpdate
} from "../mutations";
import { TypedSaleDetails } from "../queries";
import { SaleCataloguesAdd } from "../types/SaleCataloguesAdd";
import { SaleCataloguesRemove } from "../types/SaleCataloguesRemove";
import { SaleDelete } from "../types/SaleDelete";
import { SaleUpdate } from "../types/SaleUpdate";
import {
  saleListUrl,
  saleUrl,
  SaleUrlDialog,
  SaleUrlQueryParams
} from "../urls";

const PAGINATE_BY = 20;

interface SaleDetailsProps {
  id: string;
  params: SaleUrlQueryParams;
}

function discountValueTypeEnum(type: SaleType): DiscountValueTypeEnum {
  return type.toString() === DiscountValueTypeEnum.FIXED
    ? DiscountValueTypeEnum.FIXED
    : DiscountValueTypeEnum.PERCENTAGE;
}

export const SaleDetails: React.StatelessComponent<SaleDetailsProps> = ({
  id,
  params
}) => {
  const navigate = useNavigator();
  const paginate = usePaginator();
  const notify = useNotifier();
  const shop = useShop();
  const { isSelected, listElements, reset, toggle } = useBulkActions(
    params.ids
  );

  const paginationState = createPaginationState(PAGINATE_BY, params);
  const changeTab = (tab: SaleDetailsPageTab) => {
    reset();
    navigate(
      saleUrl(id, {
        activeTab: tab
      })
    );
  };

  const handleSaleDelete = (data: SaleDelete) => {
    if (data.saleDelete.errors.length === 0) {
      notify({
        text: i18n.t("Removed sale", {
          context: "notification"
        })
      });
      navigate(saleListUrl(), true);
    }
  };

  const handleSaleUpdate = (data: SaleUpdate) => {
    if (data.saleUpdate.errors.length === 0) {
      notify({
        text: i18n.t("Updated sale", {
          context: "notification"
        })
      });
    }
  };

  const closeModal = () =>
    navigate(
      saleUrl(id, {
        ...params,
        action: undefined,
        ids: undefined
      }),
      true
    );

  const openModal = (action: SaleUrlDialog, ids?: string[]) =>
    navigate(
      saleUrl(id, {
        ...params,
        action,
        ids
      })
    );

  const handleCatalogueAdd = (data: SaleCataloguesAdd) => {
    if (data.saleCataloguesAdd.errors.length === 0) {
      closeModal();
    }
  };

  const handleCatalogueRemove = (data: SaleCataloguesRemove) => {
    if (data.saleCataloguesRemove.errors.length === 0) {
      closeModal();
      reset();
    }
  };

  return (
    <TypedSaleCataloguesRemove onCompleted={handleCatalogueRemove}>
      {(saleCataloguesRemove, saleCataloguesRemoveOpts) => (
        <TypedSaleCataloguesAdd onCompleted={handleCatalogueAdd}>
          {(saleCataloguesAdd, saleCataloguesAddOpts) => (
            <TypedSaleUpdate onCompleted={handleSaleUpdate}>
              {(saleUpdate, saleUpdateOpts) => (
                <TypedSaleDelete onCompleted={handleSaleDelete}>
                  {(saleDelete, saleDeleteOpts) => (
                    <TypedSaleDetails
                      displayLoader
                      variables={{ id, ...paginationState }}
                    >
                      {({ data, loading }) => {
                        const tabPageInfo =
                          params.activeTab === SaleDetailsPageTab.categories
                            ? maybe(() => data.sale.categories.pageInfo)
                            : params.activeTab ===
                              SaleDetailsPageTab.collections
                            ? maybe(() => data.sale.collections.pageInfo)
                            : maybe(() => data.sale.products.pageInfo);
                        const formTransitionState = getMutationState(
                          saleUpdateOpts.called,
                          saleUpdateOpts.loading,
                          maybe(() => saleUpdateOpts.data.saleUpdate.errors)
                        );
                        const assignTransitionState = getMutationState(
                          saleCataloguesAddOpts.called,
                          saleCataloguesAddOpts.loading,
                          maybe(
                            () =>
                              saleCataloguesAddOpts.data.saleCataloguesAdd
                                .errors
                          )
                        );
                        const unassignTransitionState = getMutationState(
                          saleCataloguesRemoveOpts.called,
                          saleCataloguesRemoveOpts.loading,
                          maybe(
                            () =>
                              saleCataloguesRemoveOpts.data.saleCataloguesRemove
                                .errors
                          )
                        );
                        const removeTransitionState = getMutationState(
                          saleDeleteOpts.called,
                          saleDeleteOpts.loading,
                          maybe(() => saleDeleteOpts.data.saleDelete.errors)
                        );

                        const handleCategoriesUnassign = (ids: string[]) =>
                          saleCataloguesRemove({
                            variables: {
                              ...paginationState,
                              id,
                              input: {
                                categories: ids
                              }
                            }
                          });

                        const handleCollectionsUnassign = (ids: string[]) =>
                          saleCataloguesRemove({
                            variables: {
                              ...paginationState,
                              id,
                              input: {
                                collections: ids
                              }
                            }
                          });

                        const handleProductsUnassign = (ids: string[]) =>
                          saleCataloguesRemove({
                            variables: {
                              ...paginationState,
                              id,
                              input: {
                                products: ids
                              }
                            }
                          });

                        const {
                          loadNextPage,
                          loadPreviousPage,
                          pageInfo
                        } = paginate(tabPageInfo, paginationState, params);

                        return (
                          <>
                            <WindowTitle title={i18n.t("Sales")} />
                            <SaleDetailsPage
                              defaultCurrency={maybe(
                                () => shop.defaultCurrency
                              )}
                              sale={maybe(() => data.sale)}
                              disabled={
                                loading || saleCataloguesRemoveOpts.loading
                              }
                              errors={maybe(
                                () => saleUpdateOpts.data.saleUpdate.errors
                              )}
                              pageInfo={pageInfo}
                              onNextPage={loadNextPage}
                              onPreviousPage={loadPreviousPage}
                              onCategoryAssign={() =>
                                openModal("assign-category")
                              }
                              onCategoryClick={id => () =>
                                navigate(categoryUrl(id))}
                              onCollectionAssign={() =>
                                openModal("assign-collection")
                              }
                              onCollectionUnassign={collectionId =>
                                handleCollectionsUnassign([collectionId])
                              }
                              onCategoryUnassign={categoryId =>
                                handleCategoriesUnassign([categoryId])
                              }
                              onCollectionClick={id => () =>
                                navigate(collectionUrl(id))}
                              onProductAssign={() =>
                                openModal("assign-product")
                              }
                              onProductUnassign={productId =>
                                handleProductsUnassign([productId])
                              }
                              onProductClick={id => () =>
                                navigate(productUrl(id))}
                              activeTab={params.activeTab}
                              onBack={() => navigate(saleListUrl())}
                              onTabClick={changeTab}
                              onSubmit={formData =>
                                saleUpdate({
                                  variables: {
                                    id,
                                    input: {
                                      endDate:
                                        formData.endDate === ""
                                          ? null
                                          : formData.endDate,
                                      name: formData.name,
                                      startDate:
                                        formData.startDate === ""
                                          ? null
                                          : formData.startDate,
                                      type: discountValueTypeEnum(
                                        formData.type
                                      ),
                                      value: decimal(formData.value)
                                    }
                                  }
                                })
                              }
                              onRemove={() => openModal("remove")}
                              saveButtonBarState={formTransitionState}
                              categoryListToolbar={
                                <Button
                                  color="primary"
                                  onClick={() =>
                                    openModal("unassign-category", listElements)
                                  }
                                >
                                  {i18n.t("Unassign")}
                                </Button>
                              }
                              collectionListToolbar={
                                <Button
                                  color="primary"
                                  onClick={() =>
                                    openModal(
                                      "unassign-collection",
                                      listElements
                                    )
                                  }
                                >
                                  {i18n.t("Unassign")}
                                </Button>
                              }
                              productListToolbar={
                                <Button
                                  color="primary"
                                  onClick={() =>
                                    openModal("unassign-product", listElements)
                                  }
                                >
                                  {i18n.t("Unassign")}
                                </Button>
                              }
                              isChecked={isSelected}
                              selected={listElements.length}
                              toggle={toggle}
                            />
                            <SearchProductsProvider>
                              {(searchProducts, searchProductsOpts) => (
                                <AssignProductDialog
                                  confirmButtonState={assignTransitionState}
                                  open={params.action === "assign-product"}
                                  onFetch={searchProducts}
                                  loading={searchProductsOpts.loading}
                                  onClose={closeModal}
                                  onSubmit={formData =>
                                    saleCataloguesAdd({
                                      variables: {
                                        ...paginationState,
                                        id,
                                        input: {
                                          products: formData.products.map(
                                            product => product.id
                                          )
                                        }
                                      }
                                    })
                                  }
                                  products={maybe(() =>
                                    searchProductsOpts.data.products.edges
                                      .map(edge => edge.node)
                                      .filter(
                                        suggestedProduct => suggestedProduct.id
                                      )
                                  )}
                                />
                              )}
                            </SearchProductsProvider>
                            <SearchCategoriesProvider>
                              {(searchCategories, searchCategoriesOpts) => (
                                <AssignCategoriesDialog
                                  categories={maybe(() =>
                                    searchCategoriesOpts.data.categories.edges
                                      .map(edge => edge.node)
                                      .filter(
                                        suggestedCategory =>
                                          suggestedCategory.id
                                      )
                                  )}
                                  confirmButtonState={assignTransitionState}
                                  open={params.action === "assign-category"}
                                  onFetch={searchCategories}
                                  loading={searchCategoriesOpts.loading}
                                  onClose={closeModal}
                                  onSubmit={formData =>
                                    saleCataloguesAdd({
                                      variables: {
                                        ...paginationState,
                                        id,
                                        input: {
                                          categories: formData.categories.map(
                                            product => product.id
                                          )
                                        }
                                      }
                                    })
                                  }
                                />
                              )}
                            </SearchCategoriesProvider>
                            <SearchCollectionsProvider>
                              {(searchCollections, searchCollectionsOpts) => (
                                <AssignCollectionDialog
                                  collections={maybe(() =>
                                    searchCollectionsOpts.data.collections.edges
                                      .map(edge => edge.node)
                                      .filter(
                                        suggestedCategory =>
                                          suggestedCategory.id
                                      )
                                  )}
                                  confirmButtonState={assignTransitionState}
                                  open={params.action === "assign-collection"}
                                  onFetch={searchCollections}
                                  loading={searchCollectionsOpts.loading}
                                  onClose={closeModal}
                                  onSubmit={formData =>
                                    saleCataloguesAdd({
                                      variables: {
                                        ...paginationState,
                                        id,
                                        input: {
                                          collections: formData.collections.map(
                                            product => product.id
                                          )
                                        }
                                      }
                                    })
                                  }
                                />
                              )}
                            </SearchCollectionsProvider>
                            <ActionDialog
                              open={params.action === "unassign-category"}
                              title={i18n.t("Unassign Categories From Sale")}
                              confirmButtonState={unassignTransitionState}
                              onClose={closeModal}
                              onConfirm={() =>
                                handleCategoriesUnassign(params.ids)
                              }
                            >
                              <DialogContentText
                                dangerouslySetInnerHTML={{
                                  __html: i18n.t(
                                    "Are you sure you want to unassign <strong>{{ saleName }}</strong> categories?",
                                    {
                                      saleName: maybe(
                                        () => params.ids.length.toString(),
                                        "..."
                                      )
                                    }
                                  )
                                }}
                              />
                            </ActionDialog>
                            <ActionDialog
                              open={params.action === "unassign-collection"}
                              title={i18n.t("Unassign Collections From Sale")}
                              confirmButtonState={unassignTransitionState}
                              onClose={closeModal}
                              onConfirm={() =>
                                handleCollectionsUnassign(params.ids)
                              }
                            >
                              <DialogContentText
                                dangerouslySetInnerHTML={{
                                  __html: i18n.t(
                                    "Are you sure you want to unassign <strong>{{ saleName }}</strong> collections?",
                                    {
                                      saleName: maybe(
                                        () => params.ids.length.toString(),
                                        "..."
                                      )
                                    }
                                  )
                                }}
                              />
                            </ActionDialog>
                            <ActionDialog
                              open={params.action === "unassign-product"}
                              title={i18n.t("Unassign Products From Sale")}
                              confirmButtonState={unassignTransitionState}
                              onClose={closeModal}
                              onConfirm={() =>
                                handleProductsUnassign(params.ids)
                              }
                            >
                              <DialogContentText
                                dangerouslySetInnerHTML={{
                                  __html: i18n.t(
                                    "Are you sure you want to unassign <strong>{{ saleName }}</strong> products?",
                                    {
                                      saleName: maybe(
                                        () => params.ids.length.toString(),
                                        "..."
                                      )
                                    }
                                  )
                                }}
                              />
                            </ActionDialog>
                            <ActionDialog
                              open={params.action === "remove"}
                              title={i18n.t("Remove Sale")}
                              confirmButtonState={removeTransitionState}
                              onClose={closeModal}
                              variant="delete"
                              onConfirm={() =>
                                saleDelete({
                                  variables: { id }
                                })
                              }
                            >
                              <DialogContentText
                                dangerouslySetInnerHTML={{
                                  __html: i18n.t(
                                    "Are you sure you want to remove <strong>{{ saleName }}</strong>?",
                                    {
                                      saleName: maybe(
                                        () => data.sale.name,
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
                    </TypedSaleDetails>
                  )}
                </TypedSaleDelete>
              )}
            </TypedSaleUpdate>
          )}
        </TypedSaleCataloguesAdd>
      )}
    </TypedSaleCataloguesRemove>
  );
};
export default SaleDetails;
