import React from "react";

import useListSettings from "@saleor/hooks/useListSettings";
import useNavigator from "@saleor/hooks/useNavigator";
import useNotifier from "@saleor/hooks/useNotifier";
import usePaginator, {
  createPaginationState
} from "@saleor/hooks/usePaginator";

import { configurationMenuUrl } from "@saleor/configuration";
import i18n from "@saleor/i18n";
import { getMutationState, maybe } from "@saleor/misc";
import { Lists } from "@saleor/types";
import StaffAddMemberDialog, {
  FormData as AddStaffMemberForm
} from "../components/StaffAddMemberDialog";
import StaffListPage from "../components/StaffListPage";
import { TypedStaffMemberAddMutation } from "../mutations";
import { TypedStaffListQuery } from "../queries";
import { StaffMemberAdd } from "../types/StaffMemberAdd";
import {
  staffListUrl,
  StaffListUrlQueryParams,
  staffMemberDetailsUrl
} from "../urls";

interface StaffListProps {
  params: StaffListUrlQueryParams;
}

export const StaffList: React.StatelessComponent<StaffListProps> = ({
  params
}) => {
  const navigate = useNavigator();
  const notify = useNotifier();
  const paginate = usePaginator();
  const { updateListSettings, listSettings } = useListSettings(
    Lists.STAFF_MEMBERS_LIST
  );

  const closeModal = () =>
    navigate(
      staffListUrl({
        ...params,
        action: undefined,
        ids: undefined
      }),
      true
    );

  const paginationState = createPaginationState(
    listSettings.STAFF_MEMBERS_LIST.rowNumber,
    params
  );
  return (
    <TypedStaffListQuery displayLoader variables={paginationState}>
      {({ data, loading }) => {
        const handleStaffMemberAddSuccess = (data: StaffMemberAdd) => {
          if (data.staffCreate.errors.length === 0) {
            notify({
              text: i18n.t("Succesfully added staff member")
            });
            navigate(staffMemberDetailsUrl(data.staffCreate.user.id));
          }
        };

        return (
          <TypedStaffMemberAddMutation
            onCompleted={handleStaffMemberAddSuccess}
          >
            {(addStaffMember, addStaffMemberData) => {
              const handleStaffMemberAdd = (variables: AddStaffMemberForm) =>
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

              return (
                <>
                  <StaffListPage
                    disabled={loading || addStaffMemberData.loading}
                    listSettings={listSettings.STAFF_MEMBERS_LIST}
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
                    onUpdateListSettings={updateListSettings}
                    onRowClick={id => () => navigate(staffMemberDetailsUrl(id))}
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
                </>
              );
            }}
          </TypedStaffMemberAddMutation>
        );
      }}
    </TypedStaffListQuery>
  );
};

export default StaffList;
