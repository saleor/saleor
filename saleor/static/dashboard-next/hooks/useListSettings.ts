import useLocalStorage from "@saleor/hooks/useLocalStorage";
import { AppListViewSettings, defaultListSettings } from "./../config";
import { ListSettings, ListViews } from "./../types";

export interface UseListSettings<TColumns extends string = string> {
  settings: ListSettings<TColumns>;
  updateListSettings: (key: keyof ListSettings<TColumns>, value: any) => void;
}
export default function useListSettings<TColumns extends string = string>(
  listName: ListViews
): UseListSettings<TColumns> {
  const [settings, setListSettings] = useLocalStorage<AppListViewSettings>(
    "listConfig",
    defaultListSettings
  );

  const updateListSettings = (key: keyof ListSettings, value: any) =>
    setListSettings(settings => ({
      ...settings,
      [listName]: {
        ...settings[listName],
        [key]: value
      }
    }));

  return {
    settings: settings[listName] as ListSettings<TColumns>,
    updateListSettings
  };
}
