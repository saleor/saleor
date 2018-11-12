import * as React from "react";

import { staffMemberDetailsUrl } from "..";
import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import { createPaginationState, Paginator } from "../../components/Paginator";
import i18n from "../../i18n";
import { maybe } from "../../misc";
import { FormData as AddStaffMemberForm } from "../components/StaffAddMemberDialog";
import StaffListPage from "../components/StaffListPage";
import { TypedStaffMemberAddMutation } from "../mutations";
import { TypedStaffListQuery } from "../queries";
import { StaffMemberAdd } from "../types/StaffMemberAdd";

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
            <TypedStaffListQuery variables={paginationState}>
              {({ data, loading }) => {
                const handleStaffMemberAddSuccess = (data: StaffMemberAdd) => {
                  if (!maybe(() => data.staffCreate.errors.length)) {
                    pushMessage({
                      text: i18n.t("Succesfully added staff member")
                    });
                    navigate(
                      staffMemberDetailsUrl(
                        encodeURIComponent(data.staffCreate.user.id)
                      )
                    );
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
                      return (
                        <Paginator
                          pageInfo={maybe(() => data.staffUsers.pageInfo)}
                          paginationState={paginationState}
                          queryString={params}
                        >
                          {({ loadNextPage, loadPreviousPage, pageInfo }) => (
                            <StaffListPage
                              disabled={loading || addStaffMemberData.loading}
                              errors={maybe(
                                () =>
                                  addStaffMemberData.data.staffCreate.errors,
                                []
                              )}
                              pageInfo={pageInfo}
                              staffMembers={maybe(() =>
                                data.staffUsers.edges.map(edge => edge.node)
                              )}
                              onAdd={handleStaffMemberAdd}
                              onNextPage={loadNextPage}
                              onPreviousPage={loadPreviousPage}
                              onRowClick={id => () =>
                                navigate(
                                  staffMemberDetailsUrl(encodeURIComponent(id))
                                )}
                            />
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
