import { withStyles } from "@material-ui/core/styles";
import * as React from "react";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import { maybe } from "../../../misc";
import { StaffMemberDetails_user } from "../../types/StaffMemberDetails";
import StaffProperties from "../StaffProperties/StaffProperties";

interface FormData {
  hasFullAccess: boolean;
  isActive: boolean;
  permissions: string[];
}

export interface StaffDetailsPageProps {
  disabled: boolean;
  staffMember: StaffMemberDetails_user;
  onBack: () => void;
  onDelete: () => void;
  onSubmit: (data: FormData) => void;
}

const decorate = withStyles(theme => ({
  card: {
    marginBottom: theme.spacing.unit * 2
  },
  root: {
    display: "grid" as "grid",
    gridColumnGap: theme.spacing.unit * 2,
    gridTemplateColumns: "9fr 4fr"
  }
}));
const StaffDetailsPage = decorate<StaffDetailsPageProps>(
  ({ classes, staffMember, onBack }) => {
    const initialForm: FormData = {
      hasFullAccess
    };
    return (
      <Form initial={initialForm}>
        {({ change, data, hasChanged }) => (
          <Container width="md">
            <PageHeader
              title={maybe(() => staffMember.email)}
              onBack={onBack}
            />
            <div className={classes.root}>
              <div>
                <StaffProperties
                  className={classes.card}
                  staffMember={staffMember}
                />
              </div>
              <div />
            </div>
          </Container>
        )}
      </Form>
    );
  }
);
StaffDetailsPage.displayName = "StaffDetailsPage";
export default StaffDetailsPage;
