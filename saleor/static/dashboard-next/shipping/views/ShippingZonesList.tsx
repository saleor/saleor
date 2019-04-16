import DialogContentText from "@material-ui/core/DialogContentText";
import IconButton from "@material-ui/core/IconButton";
import DeleteIcon from "@material-ui/icons/Delete";
import * as React from "react";

import ActionDialog from "../../components/ActionDialog";
import { createPaginationState } from "../../components/Paginator";
import { configurationMenuUrl } from "../../configuration";
import useBulkActions from "../../hooks/useBulkActions";
import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import usePaginator from "../../hooks/usePaginator";
import useShop from "../../hooks/useShop";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import ShippingZonesListPage from "../components/ShippingZonesListPage";
import {
  TypedBulkDeleteShippingZone,
  TypedDeleteShippingZone,
  TypedUpdateDefaultWeightUnit
} from "../mutations";
import { TypedShippingZones } from "../queries";
import { BulkDeleteShippingZone } from "../types/BulkDeleteShippingZone";
import { DeleteShippingZone } from "../types/DeleteShippingZone";
import { UpdateDefaultWeightUnit } from "../types/UpdateDefaultWeightUnit";
import {
  shippingZoneAddUrl,
  shippingZonesListUrl,
  ShippingZonesListUrlQueryParams,
  shippingZoneUrl
} from "../urls";

interface ShippingZonesListProps {
  params: ShippingZonesListUrlQueryParams;
}

const PAGINATE_BY = 20;

export const ShippingZonesList: React.StatelessComponent<
  ShippingZonesListProps
> = ({ params }) => {
  const navigate = useNavigator();
  const notify = useNotifier();
  const paginate = usePaginator();
  const shop = useShop();
  const { isSelected, listElements, reset, toggle } = useBulkActions(
    params.ids
  );

  const paginationState = createPaginationState(PAGINATE_BY, params);

  return (
    <TypedShippingZones displayLoader variables={paginationState}>
      {({ data, loading, refetch }) => {
        const handleUpdateDefaultWeightUnit = (
          data: UpdateDefaultWeightUnit
        ) => {
          if (data.shopSettingsUpdate.errors.length === 0) {
            notify({
              text: i18n.t("Updated default weight unit", {
                context: "notification"
              })
            });
          }
        };

        const closeModal = () =>
          navigate(
            shippingZonesListUrl({
              ...params,
              action: undefined,
              ids: undefined
            }),
            true
          );

        const handleShippingZoneDelete = (data: DeleteShippingZone) => {
          if (data.shippingZoneDelete.errors.length === 0) {
            notify({
              text: i18n.t("Updated default weight unit", {
                context: "notification"
              })
            });
            closeModal();
            refetch();
          }
        };

        const handleBulkDeleteShippingZone = (data: BulkDeleteShippingZone) => {
          if (data.shippingZoneBulkDelete.errors.length === 0) {
            notify({
              text: i18n.t("Removed shipping zones", {
                context: "notification"
              })
            });
            closeModal();
            reset();
            refetch();
          }
        };
        return (
          <TypedDeleteShippingZone onCompleted={handleShippingZoneDelete}>
            {(deleteShippingZone, deleteShippingZoneOpts) => (
              <TypedUpdateDefaultWeightUnit
                onCompleted={handleUpdateDefaultWeightUnit}
              >
                {(updateDefaultWeightUnit, updateDefaultWeightUnitOpts) => (
                  <TypedBulkDeleteShippingZone
                    onCompleted={handleBulkDeleteShippingZone}
                  >
                    {(bulkDeleteShippingZone, bulkDeleteShippingZoneOpts) => {
                      const deleteTransitionState = getMutationState(
                        deleteShippingZoneOpts.called,
                        deleteShippingZoneOpts.loading,
                        maybe(
                          () =>
                            deleteShippingZoneOpts.data.shippingZoneDelete
                              .errors
                        )
                      );

                      const bulkDeleteTransitionState = getMutationState(
                        bulkDeleteShippingZoneOpts.called,
                        bulkDeleteShippingZoneOpts.loading,
                        maybe(
                          () =>
                            bulkDeleteShippingZoneOpts.data
                              .shippingZoneBulkDelete.errors
                        )
                      );

                      const {
                        loadNextPage,
                        loadPreviousPage,
                        pageInfo
                      } = paginate(
                        maybe(() => data.shippingZones.pageInfo),
                        paginationState,
                        params
                      );

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
                              data.shippingZones.edges.map(edge => edge.node)
                            )}
                            pageInfo={pageInfo}
                            onAdd={() => navigate(shippingZoneAddUrl)}
                            onBack={() => navigate(configurationMenuUrl)}
                            onNextPage={loadNextPage}
                            onPreviousPage={loadPreviousPage}
                            onRemove={id =>
                              navigate(
                                shippingZonesListUrl({
                                  ...params,
                                  action: "remove",
                                  id
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
                            isChecked={isSelected}
                            selected={listElements.length}
                            toggle={toggle}
                            toolbar={
                              <IconButton
                                color="primary"
                                onClick={() =>
                                  navigate(
                                    shippingZonesListUrl({
                                      action: "remove-many",
                                      ids: listElements
                                    })
                                  )
                                }
                              >
                                <DeleteIcon />
                              </IconButton>
                            }
                          />

                          <ActionDialog
                            open={params.action === "remove"}
                            confirmButtonState={deleteTransitionState}
                            variant="delete"
                            title={i18n.t("Delete Shipping Zone", {
                              context: "modal title"
                            })}
                            onClose={closeModal}
                            onConfirm={() =>
                              deleteShippingZone({
                                variables: { id: params.id }
                              })
                            }
                          >
                            <DialogContentText
                              dangerouslySetInnerHTML={{
                                __html: i18n.t(
                                  "Are you sure you want to remove <strong>{{ name }}</strong> shipping zone?",
                                  {
                                    context: "shipping zone removal",
                                    name: maybe(
                                      () =>
                                        data.shippingZones.edges.find(
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
                            confirmButtonState={bulkDeleteTransitionState}
                            variant="delete"
                            title={i18n.t("Delete Shipping Zones", {
                              context: "modal title"
                            })}
                            onClose={closeModal}
                            onConfirm={() =>
                              bulkDeleteShippingZone({
                                variables: { ids: params.ids }
                              })
                            }
                          >
                            <DialogContentText
                              dangerouslySetInnerHTML={{
                                __html: i18n.t(
                                  "Are you sure you want to remove <strong>{{ number }}</strong> shipping zones?",
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
                  </TypedBulkDeleteShippingZone>
                )}
              </TypedUpdateDefaultWeightUnit>
            )}
          </TypedDeleteShippingZone>
        );
      }}
    </TypedShippingZones>
  );
};
ShippingZonesList.displayName = "ShippingZonesList";
export default ShippingZonesList;
