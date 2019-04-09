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

  const paginationState = createPaginationState(PAGINATE_BY, params);
  const changeTab = (tab: SaleDetailsPageTab) =>
    navigate(
      saleUrl(id, {
        activeTab: tab
      })
    );

  const handleCatalogueAdd = (data: SaleCataloguesAdd) => {
    if (data.saleCataloguesAdd.errors.length === 0) {
      closeModal();
    }
  };

  const handleSaleDelete = (data: SaleDelete) => {
    if (data.saleDelete.errors.length === 0) {
      notify({
        text: i18n.t("Removed sale", {
          context: "notification"
        })
      });
      navigate(saleListUrl, true);
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
        action: undefined
      }),
      true
    );

  const openModal = (action: SaleUrlDialog) =>
    navigate(
      saleUrl(id, {
        ...params,
        action
      })
    );

  return (
    <TypedSaleCataloguesRemove>
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
                        const removeTransitionState = getMutationState(
                          saleDeleteOpts.called,
                          saleDeleteOpts.loading,
                          maybe(() => saleDeleteOpts.data.saleDelete.errors)
                        );

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
                                saleCataloguesRemove({
                                  variables: {
                                    ...paginationState,
                                    id,
                                    input: {
                                      collections: [collectionId]
                                    }
                                  }
                                })
                              }
                              onCategoryUnassign={categoryId =>
                                saleCataloguesRemove({
                                  variables: {
                                    ...paginationState,
                                    id,
                                    input: {
                                      categories: [categoryId]
                                    }
                                  }
                                })
                              }
                              onCollectionClick={id => () =>
                                navigate(collectionUrl(id))}
                              onProductAssign={() =>
                                openModal("assign-product")
                              }
                              onProductUnassign={productId =>
                                saleCataloguesRemove({
                                  variables: {
                                    ...paginationState,
                                    id,
                                    input: {
                                      products: [productId]
                                    }
                                  }
                                })
                              }
                              onProductClick={id => () =>
                                navigate(productUrl(id))}
                              activeTab={params.activeTab}
                              onBack={() => navigate(saleListUrl)}
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
