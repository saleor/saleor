import DialogContentText from "@material-ui/core/DialogContentText";
import { stringify as stringifyQs } from "qs";
import * as React from "react";
import { Route } from "react-router-dom";

import { categoryUrl } from "../../../categories/urls";
import { collectionUrl } from "../../../collections/urls";
import ActionDialog from "../../../components/ActionDialog";
import AssignCategoriesDialog from "../../../components/AssignCategoryDialog";
import AssignCollectionDialog from "../../../components/AssignCollectionDialog";
import AssignProductDialog from "../../../components/AssignProductDialog";
import Messages from "../../../components/messages";
import Navigator from "../../../components/Navigator";
import {
  createPaginationState,
  Paginator
} from "../../../components/Paginator";
import Shop from "../../../components/Shop";
import { WindowTitle } from "../../../components/WindowTitle";
import { SearchCategoriesProvider } from "../../../containers/SearchCategories";
import { SearchCollectionsProvider } from "../../../containers/SearchCollections";
import { SearchProductsProvider } from "../../../containers/SearchProducts";
import i18n from "../../../i18n";
import { getMutationState, maybe } from "../../../misc";
import { productUrl } from "../../../products/urls";
import {
  DiscountValueTypeEnum,
  VoucherDiscountValueType
} from "../../../types/globalTypes";
import VoucherDetailsPage, {
  VoucherDetailsPageTab
} from "../../components/VoucherDetailsPage";
import {
  TypedVoucherCataloguesAdd,
  TypedVoucherCataloguesRemove,
  TypedVoucherDelete,
  TypedVoucherUpdate
} from "../../mutations";
import { TypedVoucherDetails } from "../../queries";
import { VoucherDelete } from "../../types/VoucherDelete";
import { voucherListUrl, voucherUrl } from "../../urls";
import {
  voucherAssignCategoriesPath,
  voucherAssignCategoriesUrl,
  voucherAssignCollectionsPath,
  voucherAssignCollectionsUrl,
  voucherAssignCountriesUrl,
  voucherAssignProductsPath,
  voucherAssignProductsUrl,
  voucherDeletePath,
  voucherDeleteUrl
} from "./urls";
import { VoucherCataloguesAdd } from "../../types/VoucherCataloguesAdd";

const PAGINATE_BY = 20;

export type VoucherDetailsQueryParams = Partial<{
  after: string;
  before: string;
  tab: VoucherDetailsPageTab;
}>;

interface VoucherDetailsProps {
  id: string;
  params: VoucherDetailsQueryParams;
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
}) => (
  <>
    <WindowTitle title={i18n.t("Vouchers")} />
    <Shop>
      {shop => (
        <Messages>
          {pushMessage => (
            <Navigator>
              {navigate => {
                const paginationState = createPaginationState(
                  PAGINATE_BY,
                  params
                );
                const changeTab = (tab: VoucherDetailsPageTab) =>
                  navigate(
                    "?" +
                      stringifyQs({
                        tab
                      })
                  );

                const handleCatalogueAdd = (data: VoucherCataloguesAdd) => {
                  if (data.voucherCataloguesAdd.errors.length === 0) {
                    navigate(voucherUrl(id), true, true);
                  }
                };
                const handleVoucherDelete = (data: VoucherDelete) => {
                  if (data.voucherDelete.errors.length === 0) {
                    pushMessage({
                      text: i18n.t("Removed voucher", {
                        context: "notification"
                      })
                    });
                    navigate(voucherListUrl, true);
                  }
                };

                return (
                  <TypedVoucherCataloguesRemove>
                    {(voucherCataloguesRemove, voucherCataloguesRemoveOpts) => (
                      <TypedVoucherCataloguesAdd
                        onCompleted={handleCatalogueAdd}
                      >
                        {(voucherCataloguesAdd, voucherCataloguesAddOpts) => (
                          <TypedVoucherUpdate>
                            {(voucherUpdate, voucherUpdateOpts) => (
                              <TypedVoucherDelete
                                onCompleted={handleVoucherDelete}
                              >
                                {(voucherDelete, voucherDeleteOpts) => (
                                  <TypedVoucherDetails
                                    displayLoader
                                    variables={{ id, ...paginationState }}
                                  >
                                    {({ data, loading }) => {
                                      const pageInfo =
                                        params.tab ===
                                        VoucherDetailsPageTab.categories
                                          ? maybe(
                                              () =>
                                                data.voucher.categories.pageInfo
                                            )
                                          : params.tab ===
                                            VoucherDetailsPageTab.collections
                                          ? maybe(
                                              () =>
                                                data.voucher.collections
                                                  .pageInfo
                                            )
                                          : maybe(
                                              () =>
                                                data.voucher.products.pageInfo
                                            );
                                      const formTransitionState = getMutationState(
                                        voucherUpdateOpts.called,
                                        voucherUpdateOpts.loading,
                                        maybe(
                                          () =>
                                            voucherUpdateOpts.data.voucherUpdate
                                              .errors
                                        )
                                      );
                                      const assignTransitionState = getMutationState(
                                        voucherCataloguesAddOpts.called,
                                        voucherCataloguesAddOpts.loading,
                                        maybe(
                                          () =>
                                            voucherCataloguesAddOpts.data
                                              .voucherCataloguesAdd.errors
                                        )
                                      );
                                      const removeTransitionState = getMutationState(
                                        voucherDeleteOpts.called,
                                        voucherDeleteOpts.loading,
                                        maybe(
                                          () =>
                                            voucherDeleteOpts.data.voucherDelete
                                              .errors
                                        )
                                      );

                                      return (
                                        <Paginator
                                          pageInfo={pageInfo}
                                          paginationState={paginationState}
                                          queryString={params}
                                        >
                                          {({
                                            loadNextPage,
                                            loadPreviousPage,
                                            pageInfo
                                          }) => (
                                            <>
                                              <VoucherDetailsPage
                                                defaultCurrency={maybe(
                                                  () => shop.defaultCurrency
                                                )}
                                                voucher={maybe(
                                                  () => data.voucher
                                                )}
                                                disabled={
                                                  loading ||
                                                  voucherCataloguesRemoveOpts.loading
                                                }
                                                errors={maybe(
                                                  () =>
                                                    voucherUpdateOpts.data
                                                      .voucherUpdate.errors
                                                )}
                                                pageInfo={pageInfo}
                                                onNextPage={loadNextPage}
                                                onPreviousPage={
                                                  loadPreviousPage
                                                }
                                                onCategoryAssign={() =>
                                                  navigate(
                                                    voucherAssignCategoriesUrl(
                                                      id
                                                    ),
                                                    false,
                                                    true
                                                  )
                                                }
                                                onCategoryClick={id => () =>
                                                  navigate(categoryUrl(id))}
                                                onCollectionAssign={() =>
                                                  navigate(
                                                    voucherAssignCollectionsUrl(
                                                      id
                                                    ),
                                                    false,
                                                    true
                                                  )
                                                }
                                                onCollectionUnassign={collectionId =>
                                                  voucherCataloguesRemove({
                                                    variables: {
                                                      ...paginationState,
                                                      id,
                                                      input: {
                                                        collections: [
                                                          collectionId
                                                        ]
                                                      }
                                                    }
                                                  })
                                                }
                                                onCountryAssign={() =>
                                                  navigate(
                                                    voucherAssignCountriesUrl(
                                                      id
                                                    ),
                                                    false,
                                                    true
                                                  )
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
                                                              country.code !==
                                                              countryCode
                                                          )
                                                          .map(
                                                            country =>
                                                              country.code
                                                          )
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
                                                  navigate(
                                                    voucherAssignProductsUrl(
                                                      id
                                                    ),
                                                    false,
                                                    true
                                                  )
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
                                                activeTab={params.tab}
                                                onBack={() =>
                                                  navigate(voucherListUrl)
                                                }
                                                onTabClick={changeTab}
                                                onSubmit={formData =>
                                                  voucherUpdate({
                                                    variables: {
                                                      id,
                                                      input: {
                                                        discountValue:
                                                          formData.value,
                                                        discountValueType: discountValueTypeEnum(
                                                          formData.discountType
                                                        ),
                                                        endDate:
                                                          formData.endDate ===
                                                          ""
                                                            ? null
                                                            : formData.endDate,
                                                        name: formData.name,
                                                        startDate:
                                                          formData.startDate
                                                      }
                                                    }
                                                  })
                                                }
                                                onRemove={() =>
                                                  navigate(voucherDeleteUrl(id))
                                                }
                                                saveButtonBarState={
                                                  formTransitionState
                                                }
                                              />
                                              <Route
                                                path={voucherAssignProductsPath(
                                                  ":id"
                                                )}
                                                render={({ match }) => (
                                                  <SearchProductsProvider>
                                                    {(
                                                      searchProducts,
                                                      searchProductsOpts
                                                    ) => (
                                                      <AssignProductDialog
                                                        confirmButtonState={
                                                          assignTransitionState
                                                        }
                                                        open={!!match}
                                                        onFetch={searchProducts}
                                                        loading={
                                                          searchProductsOpts.loading
                                                        }
                                                        onClose={() =>
                                                          navigate(
                                                            voucherUrl(id),
                                                            true,
                                                            true
                                                          )
                                                        }
                                                        onSubmit={formData =>
                                                          voucherCataloguesAdd({
                                                            variables: {
                                                              ...paginationState,
                                                              id,
                                                              input: {
                                                                products: formData.products.map(
                                                                  product =>
                                                                    product.id
                                                                )
                                                              }
                                                            }
                                                          })
                                                        }
                                                        products={maybe(() =>
                                                          searchProductsOpts.data.products.edges
                                                            .map(
                                                              edge => edge.node
                                                            )
                                                            .filter(
                                                              suggestedProduct =>
                                                                suggestedProduct.id
                                                            )
                                                        )}
                                                      />
                                                    )}
                                                  </SearchProductsProvider>
                                                )}
                                              />
                                              <Route
                                                path={voucherAssignCategoriesPath(
                                                  ":id"
                                                )}
                                                render={({ match }) => (
                                                  <SearchCategoriesProvider>
                                                    {(
                                                      searchCategories,
                                                      searchCategoriesOpts
                                                    ) => (
                                                      <AssignCategoriesDialog
                                                        categories={maybe(() =>
                                                          searchCategoriesOpts.data.categories.edges
                                                            .map(
                                                              edge => edge.node
                                                            )
                                                            .filter(
                                                              suggestedCategory =>
                                                                suggestedCategory.id
                                                            )
                                                        )}
                                                        confirmButtonState={
                                                          assignTransitionState
                                                        }
                                                        open={!!match}
                                                        onFetch={
                                                          searchCategories
                                                        }
                                                        loading={
                                                          searchCategoriesOpts.loading
                                                        }
                                                        onClose={() =>
                                                          navigate(
                                                            voucherUrl(id),
                                                            true,
                                                            true
                                                          )
                                                        }
                                                        onSubmit={formData =>
                                                          voucherCataloguesAdd({
                                                            variables: {
                                                              ...paginationState,
                                                              id,
                                                              input: {
                                                                categories: formData.categories.map(
                                                                  product =>
                                                                    product.id
                                                                )
                                                              }
                                                            }
                                                          })
                                                        }
                                                      />
                                                    )}
                                                  </SearchCategoriesProvider>
                                                )}
                                              />
                                              <Route
                                                path={voucherAssignCollectionsPath(
                                                  ":id"
                                                )}
                                                render={({ match }) => (
                                                  <SearchCollectionsProvider>
                                                    {(
                                                      searchCollections,
                                                      searchCollectionsOpts
                                                    ) => (
                                                      <AssignCollectionDialog
                                                        collections={maybe(() =>
                                                          searchCollectionsOpts.data.collections.edges
                                                            .map(
                                                              edge => edge.node
                                                            )
                                                            .filter(
                                                              suggestedCategory =>
                                                                suggestedCategory.id
                                                            )
                                                        )}
                                                        confirmButtonState={
                                                          assignTransitionState
                                                        }
                                                        open={!!match}
                                                        onFetch={
                                                          searchCollections
                                                        }
                                                        loading={
                                                          searchCollectionsOpts.loading
                                                        }
                                                        onClose={() =>
                                                          navigate(
                                                            voucherUrl(id),
                                                            true,
                                                            true
                                                          )
                                                        }
                                                        onSubmit={formData =>
                                                          voucherCataloguesAdd({
                                                            variables: {
                                                              ...paginationState,
                                                              id,
                                                              input: {
                                                                collections: formData.collections.map(
                                                                  product =>
                                                                    product.id
                                                                )
                                                              }
                                                            }
                                                          })
                                                        }
                                                      />
                                                    )}
                                                  </SearchCollectionsProvider>
                                                )}
                                              />
                                              <Route
                                                path={voucherDeletePath(":id")}
                                                render={({ match }) => (
                                                  <ActionDialog
                                                    open={!!match}
                                                    title={i18n.t(
                                                      "Remove Voucher"
                                                    )}
                                                    confirmButtonState={
                                                      removeTransitionState
                                                    }
                                                    onClose={() =>
                                                      navigate(voucherUrl(id))
                                                    }
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
                                                              () =>
                                                                data.voucher
                                                                  .name
                                                            )
                                                          }
                                                        )
                                                      }}
                                                    />
                                                  </ActionDialog>
                                                )}
                                              />
                                            </>
                                          )}
                                        </Paginator>
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
              }}
            </Navigator>
          )}
        </Messages>
      )}
    </Shop>
  </>
);
export default VoucherDetails;
