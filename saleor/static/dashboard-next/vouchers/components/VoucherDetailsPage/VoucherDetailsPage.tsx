import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

interface VoucherDetailsPageProps {}

const decorate = withStyles(theme => ({ root: {} }));
const VoucherDetailsPage = decorate<VoucherDetailsPageProps>(({ classes }) => <div />);
VoucherDetailsPage.displayName = "VoucherDetailsPage";
export default VoucherDetailsPage;
