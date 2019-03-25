// import Button from "@material-ui/core/Button";
// import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import { ShopInfo_shop_languages } from "../../../components/Shop/types/ShopInfo";
import i18n from "../../../i18n";
import TranslationsLanguageList from "../TranslationsLanguageList";

export interface TranslationsLanguageListPageProps {
  languages: ShopInfo_shop_languages[];
  //   onAdd: () => void;
  onRowClick: (code: string) => void;
}

const TranslationsLanguageListPage: React.StatelessComponent<
  TranslationsLanguageListPageProps
> = ({ languages, onRowClick }) => (
  <Container>
    <PageHeader title={i18n.t("Languages")}>
      {/* <Button color="primary" variant="contained" onClick={onAdd}>
        {i18n.t("Add Language")}
        <AddIcon />
      </Button> */}
    </PageHeader>
    <TranslationsLanguageList languages={languages} onRowClick={onRowClick} />
  </Container>
);
TranslationsLanguageListPage.displayName = "TranslationsLanguageListPage";
export default TranslationsLanguageListPage;
