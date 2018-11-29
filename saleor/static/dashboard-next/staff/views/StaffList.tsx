import * as React from "react";
import { Route } from "react-router-dom";

import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import { createPaginationState, Paginator } from "../../components/Paginator";
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
  staffMemberAddPath,
  staffMemberAddUrl,
  staffMemberDetailsUrl
} from "../urls";

export type StaffListQueryParams = Partial<{
  after: string;
  before: string;
}>;

interface StaffListProps {
  params: StaffListQueryParams;
}

const PAGINATE_BY = 20;

export const StaffList: React.StatelessComponent<StaffListProps> = ({
  params
}) => (
  <Navigator>
    {navigate => (
      <Messages>
        {pushMessage => {
          const paginationState = createPaginationState(PAGINATE_BY, params);
          return (
            <TypedStaffListQuery displayLoader variables={paginationState}>
              {({ data, loading }) => {
                const handleStaffMemberAddSuccess = (data: StaffMemberAdd) => {
                  if (!maybe(() => data.staffCreate.errors.length)) {
                    pushMessage({
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
                      const handleStaffMemberAdd = (
                        variables: AddStaffMemberForm
                      ) =>
                        addStaffMember({
                          variables: {
                            input: {
                              email: variables.email,
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
                      return (
                        <Paginator
                          pageInfo={maybe(() => data.staffUsers.pageInfo)}
                          paginationState={paginationState}
                          queryString={params}
                        >
                          {({ loadNextPage, loadPreviousPage, pageInfo }) => (
                            <>
                              <StaffListPage
                                disabled={loading || addStaffMemberData.loading}
                                pageInfo={pageInfo}
                                staffMembers={maybe(() =>
                                  data.staffUsers.edges.map(edge => edge.node)
                                )}
                                onAdd={() => navigate(staffMemberAddUrl)}
                                onNextPage={loadNextPage}
                                onPreviousPage={loadPreviousPage}
                                onRowClick={id => () =>
                                  navigate(staffMemberDetailsUrl(id))}
                              />
                              <Route
                                path={staffMemberAddPath}
                                render={({ match }) => (
                                  <StaffAddMemberDialog
                                    confirmButtonState={addTransitionState}
                                    errors={maybe(
                                      () =>
                                        addStaffMemberData.data.staffCreate
                                          .errors,
                                      []
                                    )}
                                    open={!!match}
                                    onClose={() => navigate(staffListUrl)}
                                    onConfirm={handleStaffMemberAdd}
                                  />
                                )}
                              />
                            </>
                          )}
                        </Paginator>
                      );
                    }}
                  </TypedStaffMemberAddMutation>
                );
              }}
            </TypedStaffListQuery>
          );
        }}
      </Messages>
    )}
  </Navigator>
);

export default StaffList;
