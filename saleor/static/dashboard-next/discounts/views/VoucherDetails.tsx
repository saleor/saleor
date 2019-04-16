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
import {
  DiscountValueTypeEnum,
  VoucherDiscountValueType
} from "../../types/globalTypes";
import DiscountCountrySelectDialog from "../components/DiscountCountrySelectDialog";
import VoucherDetailsPage, {
  VoucherDetailsPageTab
} from "../components/VoucherDetailsPage";
import {
  TypedVoucherCataloguesAdd,
  TypedVoucherCataloguesRemove,
  TypedVoucherDelete,
  TypedVoucherUpdate
} from "../mutations";
import { TypedVoucherDetails } from "../queries";
import { VoucherCataloguesAdd } from "../types/VoucherCataloguesAdd";
import { VoucherCataloguesRemove } from "../types/VoucherCataloguesRemove";
import { VoucherDelete } from "../types/VoucherDelete";
import { VoucherUpdate } from "../types/VoucherUpdate";
import {
  voucherListUrl,
  voucherUrl,
  VoucherUrlDialog,
  VoucherUrlQueryParams
} from "../urls";

const PAGINATE_BY = 20;

interface VoucherDetailsProps {
  id: string;
  params: VoucherUrlQueryParams;
}

function discountValueTypeEnum(
  type: VoucherDiscountValueType
): DiscountValueTypeEnum {
  return type.toString() === DiscountValueTypeEnum.FIXED
    ? DiscountValueTypeEnum.FIXED
    : DiscountValueTypeEnum.PERCENTAGE;
}

export const VoucherDetails: React.StatelessComponent<VoucherDetailsProps> = ({
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
  const changeTab = (tab: VoucherDetailsPageTab) => {
    reset();
    navigate(
      voucherUrl(id, {
        activeTab: tab
      })
    );
  };

  const handleVoucherDelete = (data: VoucherDelete) => {
    if (data.voucherDelete.errors.length === 0) {
      notify({
        text: i18n.t("Removed voucher", {
          context: "notification"
        })
      });
      navigate(voucherListUrl(), true);
    }
  };

  const handleVoucherUpdate = (data: VoucherUpdate) => {
    if (data.voucherUpdate.errors.length === 0) {
      closeModal();
      notify({
        text: i18n.t("Updated voucher", {
          context: "notification"
        })
      });
    }
  };

  const closeModal = () =>
    navigate(
      voucherUrl(id, {
        ...params,
        action: undefined
      }),
      true
    );

  const openModal = (action: VoucherUrlDialog, ids?: string[]) =>
    navigate(
      voucherUrl(id, {
        ...params,
        action,
        ids
      })
    );

  const handleCatalogueAdd = (data: VoucherCataloguesAdd) => {
    if (data.voucherCataloguesAdd.errors.length === 0) {
      closeModal();
    }
  };

  const handleCatalogueRemove = (data: VoucherCataloguesRemove) => {
    if (data.voucherCataloguesRemove.errors.length === 0) {
      closeModal();
      reset();
    }
  };

  return (
    <TypedVoucherCataloguesRemove onCompleted={handleCatalogueRemove}>
      {(voucherCataloguesRemove, voucherCataloguesRemoveOpts) => (
        <TypedVoucherCataloguesAdd onCompleted={handleCatalogueAdd}>
          {(voucherCataloguesAdd, voucherCataloguesAddOpts) => (
            <TypedVoucherUpdate onCompleted={handleVoucherUpdate}>
              {(voucherUpdate, voucherUpdateOpts) => (
                <TypedVoucherDelete onCompleted={handleVoucherDelete}>
                  {(voucherDelete, voucherDeleteOpts) => (
                    <TypedVoucherDetails
                      displayLoader
                      variables={{ id, ...paginationState }}
                    >
                      {({ data, loading }) => {
                        const tabPageInfo =
                          params.activeTab === VoucherDetailsPageTab.categories
                            ? maybe(() => data.voucher.categories.pageInfo)
                            : params.activeTab ===
                              VoucherDetailsPageTab.collections
                            ? maybe(() => data.voucher.collections.pageInfo)
                            : maybe(() => data.voucher.products.pageInfo);
                        const formTransitionState = getMutationState(
                          voucherUpdateOpts.called,
                          voucherUpdateOpts.loading,
                          maybe(
                            () => voucherUpdateOpts.data.voucherUpdate.errors
                          )
                        );
                        const assignTransitionState = getMutationState(
                          voucherCataloguesAddOpts.called,
                          voucherCataloguesAddOpts.loading,
                          maybe(
                            () =>
                              voucherCataloguesAddOpts.data.voucherCataloguesAdd
                                .errors
                          )
                        );
                        const unassignTransitionState = getMutationState(
                          voucherCataloguesRemoveOpts.called,
                          voucherCataloguesRemoveOpts.loading,
                          maybe(
                            () =>
                              voucherCataloguesRemoveOpts.data
                                .voucherCataloguesRemove.errors
                          )
                        );
                        const removeTransitionState = getMutationState(
                          voucherDeleteOpts.called,
                          voucherDeleteOpts.loading,
                          maybe(
                            () => voucherDeleteOpts.data.voucherDelete.errors
                          )
                        );

                        const handleCategoriesUnassign = (ids: string[]) =>
                          voucherCataloguesRemove({
                            variables: {
                              ...paginationState,
                              id,
                              input: {
                                categories: ids
                              }
                            }
                          });

                        const handleCollectionsUnassign = (ids: string[]) =>
                          voucherCataloguesRemove({
                            variables: {
                              ...paginationState,
                              id,
                              input: {
                                collections: ids
                              }
                            }
                          });

                        const handleProductsUnassign = (ids: string[]) =>
                          voucherCataloguesRemove({
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
                            <WindowTitle title={i18n.t("Vouchers")} />
                            <VoucherDetailsPage
                              defaultCurrency={maybe(
                                () => shop.defaultCurrency
                              )}
                              voucher={maybe(() => data.voucher)}
                              disabled={
                                loading || voucherCataloguesRemoveOpts.loading
                              }
                              errors={maybe(
                                () =>
                                  voucherUpdateOpts.data.voucherUpdate.errors
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
                                voucherCataloguesRemove({
                                  variables: {
                                    ...paginationState,
                                    id,
                                    input: {
                                      collections: [collectionId]
                                    }
                                  }
                                })
                              }
                              onCountryAssign={() =>
                                openModal("assign-country")
                              }
                              onCountryUnassign={countryCode =>
                                voucherUpdate({
                                  variables: {
                                    ...paginationState,
                                    id,
                                    input: {
                                      countries: data.voucher.countries
                                        .filter(
                                          country =>
                                            country.code !== countryCode
                                        )
                                        .map(country => country.code)
                                    }
                                  }
                                })
                              }
                              onCategoryUnassign={categoryId =>
                                voucherCataloguesRemove({
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
                                voucherCataloguesRemove({
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
                              onBack={() => navigate(voucherListUrl())}
                              onTabClick={changeTab}
                              onSubmit={formData =>
                                voucherUpdate({
                                  variables: {
                                    id,
                                    input: {
                                      discountValue: decimal(formData.value),
                                      discountValueType: discountValueTypeEnum(
                                        formData.discountType
                                      ),
                                      endDate:
                                        formData.endDate === ""
                                          ? null
                                          : formData.endDate,
                                      name: formData.name,
                                      startDate:
                                        formData.startDate === ""
                                          ? null
                                          : formData.startDate
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
                                    voucherCataloguesAdd({
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
                                    voucherCataloguesAdd({
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
                            <DiscountCountrySelectDialog
                              confirmButtonState={formTransitionState}
                              countries={maybe(() => shop.countries, [])}
                              onClose={() => navigate(voucherUrl(id))}
                              onConfirm={formData =>
                                voucherUpdate({
                                  variables: {
                                    id,
                                    input: {
                                      countries: formData.countries
                                    }
                                  }
                                })
                              }
                              open={params.action === "assign-country"}
                              initial={maybe(
                                () =>
                                  data.voucher.countries.map(
                                    country => country.code
                                  ),
                                []
                              )}
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
                                    voucherCataloguesAdd({
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
                              title={i18n.t("Remove Voucher")}
                              confirmButtonState={removeTransitionState}
                              onClose={closeModal}
                              variant="delete"
                              onConfirm={() =>
                                voucherDelete({
                                  variables: { id }
                                })
                              }
                            >
                              <DialogContentText
                                dangerouslySetInnerHTML={{
                                  __html: i18n.t(
                                    "Are you sure you want to remove <strong>{{ voucherName }}</strong>?",
                                    {
                                      voucherName: maybe(
                                        () => data.voucher.name,
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
                    </TypedVoucherDetails>
                  )}
                </TypedVoucherDelete>
              )}
            </TypedVoucherUpdate>
          )}
        </TypedVoucherCataloguesAdd>
      )}
    </TypedVoucherCataloguesRemove>
  );
};
export default VoucherDetails;
