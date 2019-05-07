import * as React from "react";

import { createPaginationState } from "../../components/Paginator";
import { configurationMenuUrl } from "../../configuration";
import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import usePaginator from "../../hooks/usePaginator";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
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

const PAGINATE_BY = 20;

export const StaffList: React.StatelessComponent<StaffListProps> = ({
  params
}) => {
  const navigate = useNavigator();
  const notify = useNotifier();
  const paginate = usePaginator();

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
