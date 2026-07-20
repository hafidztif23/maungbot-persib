import Card from "../common/Card";
import CustomSelect from "../common/CustomSelect";
import { useAuth } from "../../hooks/useAuth";
import { getTranslation } from "../../utils/translation";

const SYSTEM_LANGUAGE_OPTIONS = ["English", "Indonesia"];

function LanguageCard({
  systemLanguage,
  setSystemLanguage,
}) {
  const { user } = useAuth();
  const t = getTranslation(user?.referensi_bahasa);

  return (
    <Card title={t.card_language}>
      <div className="settings-row">
        <span>{t.system_lang}</span>
        <CustomSelect
          value={systemLanguage}
          options={SYSTEM_LANGUAGE_OPTIONS}
          onChange={(e) => setSystemLanguage(e.target.value)}
        />
      </div>
    </Card>
  );
}

export default LanguageCard;