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
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import StaffAddMemberDialog, {
  FormData as AddStaffMemberForm
} from "../components/StaffAddMemberDialog";
import StaffListPage from "../components/StaffListPage";
import {
  TypedStaffMemberAddMutation,
  TypedStaffMembersBulkDeleteMutation
} from "../mutations";
import { TypedStaffListQuery } from "../queries";
import { StaffMemberAdd } from "../types/StaffMemberAdd";
import { StaffMembersBulkDelete } from "../types/StaffMembersBulkDelete";
import {
  staffListUrl,
  StaffListUrlQueryParams,
  staffMemberDetailsUrl
} from "../urls";

interface StaffListProps {
  params: StaffListUrlQueryParams;
}

const PAGINATE_BY = 20;

export const StaffList: React.StatelessComponent<StaffListProps> = ({
  params
}) => {
  const navigate = useNavigator();
  const notify = useNotifier();
  const paginate = usePaginator();
  const { isSelected, listElements, reset, toggle } = useBulkActions();

  const closeModal = () =>
    navigate(
      staffListUrl({
        ...params,
        action: undefined,
        ids: undefined
      }),
      true
    );

  const paginationState = createPaginationState(PAGINATE_BY, params);
  return (
    <TypedStaffListQuery displayLoader variables={paginationState}>
      {({ data, loading, refetch }) => {
        const handleStaffMemberAddSuccess = (data: StaffMemberAdd) => {
          if (data.staffCreate.errors.length === 0) {
            notify({
              text: i18n.t("Succesfully added staff member")
            });
            navigate(staffMemberDetailsUrl(data.staffCreate.user.id));
          }
        };

        const handleStaffMembersDelete = (data: StaffMembersBulkDelete) => {
          if (data.staffBulkDelete.errors.length === 0) {
            notify({
              text: i18n.t("Removed staff members")
            });
            closeModal();
            reset();
            refetch();
          }
        };

        return (
          <TypedStaffMemberAddMutation
            onCompleted={handleStaffMemberAddSuccess}
          >
            {(addStaffMember, addStaffMemberData) => (
              <TypedStaffMembersBulkDeleteMutation
                onCompleted={handleStaffMembersDelete}
              >
                {(staffMembersBulkDelete, staffMembersBulkDeleteOpts) => {
                  const handleStaffMemberAdd = (
                    variables: AddStaffMemberForm
                  ) =>
                    addStaffMember({
                      variables: {
                        input: {
                          email: variables.email,
                          firstName: variables.firstName,
                          lastName: variables.lastName,
                          permissions: variables.fullAccess
                            ? data.shop.permissions.map(perm => perm.code)
                            : undefined,
                          sendPasswordEmail: true
                        }
                      }
                    });
                  const addTransitionState = getMutationState(
                    addStaffMemberData.called,
                    addStaffMemberData.loading,
                    maybe(() => addStaffMemberData.data.staffCreate.errors)
                  );

                  const { loadNextPage, loadPreviousPage, pageInfo } = paginate(
                    maybe(() => data.staffUsers.pageInfo),
                    paginationState,
                    params
                  );

                  const bulkRemoveTransitionState = getMutationState(
                    staffMembersBulkDeleteOpts.called,
                    staffMembersBulkDeleteOpts.loading,
                    maybe(
                      () =>
                        staffMembersBulkDeleteOpts.data.staffMembersBulkDelete
                          .errors
                    )
                  );
                  const onSaleBulkDelete = () =>
                    staffMembersBulkDelete({
                      variables: {
                        ids: params.ids
                      }
                    });

                  return (
                    <>
                      <StaffListPage
                        disabled={loading || addStaffMemberData.loading}
                        pageInfo={pageInfo}
                        staffMembers={maybe(() =>
                          data.staffUsers.edges.map(edge => edge.node)
                        )}
                        onAdd={() =>
                          navigate(
                            staffListUrl({
                              action: "add"
                            })
                          )
                        }
                        onBack={() => navigate(configurationMenuUrl)}
                        onNextPage={loadNextPage}
                        onPreviousPage={loadPreviousPage}
                        onRowClick={id => () =>
                          navigate(staffMemberDetailsUrl(id))}
                        isChecked={isSelected}
                        selected={listElements.length}
                        toggle={toggle}
                        toolbar={
                          <IconButton
                            color="primary"
                            onClick={() =>
                              navigate(
                                staffListUrl({
                                  action: "remove",
                                  ids: listElements
                                })
                              )
                            }
                          >
                            <DeleteIcon />
                          </IconButton>
                        }
                      />
                      <StaffAddMemberDialog
                        confirmButtonState={addTransitionState}
                        errors={maybe(
                          () => addStaffMemberData.data.staffCreate.errors,
                          []
                        )}
                        open={params.action === "add"}
                        onClose={closeModal}
                        onConfirm={handleStaffMemberAdd}
                      />
                      <ActionDialog
                        confirmButtonState={bulkRemoveTransitionState}
                        onClose={closeModal}
                        onConfirm={onSaleBulkDelete}
                        open={params.action === "remove"}
                        title={i18n.t("Remove Staff Members")}
                        variant="delete"
                      >
                        <DialogContentText
                          dangerouslySetInnerHTML={{
                            __html: i18n.t(
                              "Are you sure you want to remove <strong>{{ number }}</strong> staff members?",
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
              </TypedStaffMembersBulkDeleteMutation>
            )}
          </TypedStaffMemberAddMutation>
        );
      }}
    </TypedStaffListQuery>
  );
};

export default StaffList;
