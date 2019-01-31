import { stringify as stringifyQs } from "qs";
import * as React from "react";
import { Route } from "react-router-dom";

import { categoryUrl } from "../../../categories/urls";
import { collectionUrl } from "../../../collections/urls";
import AssignProductDialog from "../../../components/AssignProductDialog";
import Messages from "../../../components/messages";
import Navigator from "../../../components/Navigator";
import {
  createPaginationState,
  Paginator
} from "../../../components/Paginator";
import Shop from "../../../components/Shop";
import { WindowTitle } from "../../../components/WindowTitle";
import { SearchProductsProvider } from "../../../containers/SearchProducts";
import i18n from "../../../i18n";
import { getMutationState, maybe } from "../../../misc";
import { productUrl } from "../../../products/urls";
import { DiscountValueTypeEnum, SaleType } from "../../../types/globalTypes";
import SaleDetailsPage, {
  SaleDetailsPageTab
} from "../../components/SaleDetailsPage";
import { TypedSaleCataloguesAdd, TypedSaleUpdate } from "../../mutations";
import { TypedSaleDetails } from "../../queries";
import { SaleCataloguesAdd } from "../../types/SaleCataloguesAdd";
import { saleListUrl, saleUrl } from "../../urls";
import { saleAssignProductsPath, saleAssignProductsUrl } from "./urls";

const PAGINATE_BY = 20;

export type SaleDetailsQueryParams = Partial<{
  after: string;
  before: string;
  tab: SaleDetailsPageTab;
}>;

interface SaleDetailsProps {
  id: string;
  params: SaleDetailsQueryParams;
}

function discountValueTypeEnum(type: SaleType): DiscountValueTypeEnum {
  return type.toString() === DiscountValueTypeEnum.FIXED
    ? DiscountValueTypeEnum.FIXED
    : DiscountValueTypeEnum.PERCENTAGE;
}

export const SaleDetails: React.StatelessComponent<SaleDetailsProps> = ({
  id,
  params
}) => (
  <>
    <WindowTitle title={i18n.t("Sales")} />
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
                const changeTab = (tab: SaleDetailsPageTab) =>
                  navigate(
                    "?" +
                      stringifyQs({
                        tab
                      })
                  );

                const handleProductAssign = (data: SaleCataloguesAdd) => {
                  if (data.saleCataloguesAdd.errors.length === 0) {
                    pushMessage({
                      text: i18n.t("Added product to collection", {
                        context: "notification"
                      })
                    });
                    navigate(saleUrl(id), true);
                  }
                };

                return (
                  <TypedSaleCataloguesAdd onCompleted={handleProductAssign}>
                    {(saleCataloguesAdd, saleCataloguesAddOpts) => (
                      <TypedSaleUpdate>
                        {(saleUpdate, saleUpdateOpts) => (
                          <TypedSaleDetails
                            displayLoader
                            variables={{ id, ...paginationState }}
                          >
                            {({ data, loading }) => {
                              const pageInfo =
                                params.tab === SaleDetailsPageTab.categories
                                  ? maybe(() => data.sale.categories.pageInfo)
                                  : params.tab ===
                                    SaleDetailsPageTab.collections
                                  ? maybe(() => data.sale.collections.pageInfo)
                                  : maybe(() => data.sale.products.pageInfo);
                              const formTransitionState = getMutationState(
                                saleUpdateOpts.called,
                                saleUpdateOpts.loading,
                                maybe(
                                  () => saleUpdateOpts.data.saleUpdate.errors
                                )
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

                              return (
                                <>
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
                                      <SaleDetailsPage
                                        defaultCurrency={maybe(
                                          () => shop.defaultCurrency
                                        )}
                                        sale={maybe(() => data.sale)}
                                        disabled={loading}
                                        pageInfo={pageInfo}
                                        onNextPage={loadNextPage}
                                        onPreviousPage={loadPreviousPage}
                                        onCategoryClick={id => () =>
                                          navigate(categoryUrl(id))}
                                        onCollectionClick={id => () =>
                                          navigate(collectionUrl(id))}
                                        onProductAssign={() =>
                                          navigate(
                                            saleAssignProductsUrl(id),
                                            false,
                                            true
                                          )
                                        }
                                        onProductClick={id => () =>
                                          navigate(productUrl(id))}
                                        activeTab={params.tab}
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
                                                    : new Date(
                                                        formData.endDate
                                                      ),
                                                name: formData.name,
                                                startDate: new Date(
                                                  formData.startDate
                                                ),
                                                type: discountValueTypeEnum(
                                                  formData.type
                                                ),
                                                value: formData.value
                                              }
                                            }
                                          })
                                        }
                                        saveButtonBarState={formTransitionState}
                                      />
                                    )}
                                  </Paginator>
                                  <Route
                                    path={saleAssignProductsPath(":id")}
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
                                            loading={searchProductsOpts.loading}
                                            onClose={() =>
                                              navigate(saleUrl(id), true, true)
                                            }
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
                                                  suggestedProduct =>
                                                    suggestedProduct.id
                                                )
                                            )}
                                          />
                                        )}
                                      </SearchProductsProvider>
                                    )}
                                  />
                                </>
                              );
                            }}
                          </TypedSaleDetails>
                        )}
                      </TypedSaleUpdate>
                    )}
                  </TypedSaleCataloguesAdd>
                );
              }}
            </Navigator>
          )}
        </Messages>
      )}
    </Shop>
  </>
);
export default SaleDetails;
