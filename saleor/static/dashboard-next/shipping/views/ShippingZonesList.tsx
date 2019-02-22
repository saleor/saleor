import DialogContentText from "@material-ui/core/DialogContentText";
import { stringify as stringifyQs } from "qs";
import * as React from "react";

import ActionDialog from "../../components/ActionDialog";
import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import { createPaginationState, Paginator } from "../../components/Paginator";
import Shop from "../../components/Shop";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import { Pagination } from "../../types";
import ShippingZonesListPage from "../components/ShippingZonesListPage";
import {
  TypedDeleteShippingZone,
  TypedUpdateDefaultWeightUnit
} from "../mutations";
import { TypedShippingZones } from "../queries";
import { UpdateDefaultWeightUnit } from "../types/UpdateDefaultWeightUnit";
import { shippingZoneAddUrl, shippingZoneUrl } from "../urls";

export type ShippingZonesListQueryParams = Pagination &
  Partial<{
    delete: string;
  }>;

interface ShippingZonesListProps {
  params: ShippingZonesListQueryParams;
}

const PAGINATE_BY = 20;

export const ShippingZonesList: React.StatelessComponent<
  ShippingZonesListProps
> = ({ params }) => (
  <Navigator>
    {navigate => (
      <Messages>
        {pushMessage => (
          <Shop>
            {shop => {
              const paginationState = createPaginationState(
                PAGINATE_BY,
                params
              );
              const handleUpdateDefaultWeightUnit = (
                data: UpdateDefaultWeightUnit
              ) => {
                if (data.shopSettingsUpdate.errors.length === 0) {
                  pushMessage({
                    text: i18n.t("Updated default weight unit", {
                      context: "notification"
                    })
                  });
                }
              };

              return (
                <TypedDeleteShippingZone>
                  {(deleteShippingZone, deleteShippingZoneOpts) => (
                    <TypedUpdateDefaultWeightUnit
                      onCompleted={handleUpdateDefaultWeightUnit}
                    >
                      {(
                        updateDefaultWeightUnit,
                        updateDefaultWeightUnitOpts
                      ) => (
                        <TypedShippingZones
                          displayLoader
                          variables={paginationState}
                        >
                          {({ data, loading }) => {
                            const deleteTransitionState = getMutationState(
                              deleteShippingZoneOpts.called,
                              deleteShippingZoneOpts.loading,
                              maybe(
                                () =>
                                  deleteShippingZoneOpts.data.shippingZoneDelete
                                    .errors
                              )
                            );

                            return (
                              <Paginator
                                pageInfo={maybe(
                                  () => data.shippingZones.pageInfo
                                )}
                                paginationState={paginationState}
                                queryString={params}
                              >
                                {({
                                  loadNextPage,
                                  loadPreviousPage,
                                  pageInfo
                                }) => {
                                  return (
                                    <>
                                      <ShippingZonesListPage
                                        defaultWeightUnit={maybe(
                                          () => shop.defaultWeightUnit
                                        )}
                                        disabled={
                                          loading ||
                                          deleteShippingZoneOpts.loading ||
                                          updateDefaultWeightUnitOpts.loading
                                        }
                                        shippingZones={maybe(() =>
                                          data.shippingZones.edges.map(
                                            edge => edge.node
                                          )
                                        )}
                                        pageInfo={pageInfo}
                                        onAdd={() =>
                                          navigate(shippingZoneAddUrl)
                                        }
                                        onNextPage={loadNextPage}
                                        onPreviousPage={loadPreviousPage}
                                        onRemove={id =>
                                          navigate(
                                            "?" +
                                              stringifyQs({
                                                ...params,
                                                delete: id
                                              })
                                          )
                                        }
                                        onRowClick={id => () =>
                                          navigate(shippingZoneUrl(id))}
                                        onSubmit={unit =>
                                          updateDefaultWeightUnit({
                                            variables: { unit }
                                          })
                                        }
                                      />
                                      <ActionDialog
                                        open={!!params.delete}
                                        confirmButtonState={
                                          deleteTransitionState
                                        }
                                        variant="delete"
                                        title={i18n.t("Delete Shipping Zone", {
                                          context: "modal title"
                                        })}
                                        onClose={() =>
                                          navigate(
                                            "?" +
                                              stringifyQs({
                                                ...params,
                                                delete: undefined
                                              })
                                          )
                                        }
                                        onConfirm={() =>
                                          deleteShippingZone({
                                            variables: { id: params.delete }
                                          })
                                        }
                                      >
                                        <DialogContentText
                                          dangerouslySetInnerHTML={{
                                            __html: i18n.t(
                                              "Are you sure you want to remove <strong>{{ name }}</strong>?",
                                              {
                                                context:
                                                  "shipping zone removal",
                                                name: maybe(
                                                  () =>
                                                    data.shippingZones.edges.find(
                                                      edge =>
                                                        edge.node.id ===
                                                        params.delete
                                                    ).node.name,
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
                              </Paginator>
                            );
                          }}
                        </TypedShippingZones>
                      )}
                    </TypedUpdateDefaultWeightUnit>
                  )}
                </TypedDeleteShippingZone>
              );
            }}
          </Shop>
        )}
      </Messages>
    )}
  </Navigator>
);
ShippingZonesList.displayName = "ShippingZonesList";
export default ShippingZonesList;
