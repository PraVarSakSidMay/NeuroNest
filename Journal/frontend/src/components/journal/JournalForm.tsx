/* ──────────────────────────────────────────────────────────────
   JournalForm — Create/Edit form with Zod validation
   ────────────────────────────────────────────────────────────── */
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import Input from "../common/Input";
import TextArea from "../common/TextArea";
import MoodSelector from "./MoodSelector";
import Button from "../common/Button";
import { ALL_MOODS, type Mood } from "../../types/journal";

const journalSchema = z.object({
  title: z
    .string()
    .min(1, "Title is required")
    .max(200, "Title must be 200 characters or less"),
  content: z
    .string()
    .min(1, "Content is required")
    .max(10000, "Content must be 10,000 characters or less"),
  mood: z.enum(ALL_MOODS as [string, ...string[]], {
    required_error: "Please select a mood",
  }),
});

export type JournalFormData = z.infer<typeof journalSchema>;

interface JournalFormProps {
  defaultValues?: Partial<JournalFormData>;
  onSubmit: (data: JournalFormData) => Promise<void>;
  submitLabel?: string;
  loading?: boolean;
}

export default function JournalForm({
  defaultValues,
  onSubmit,
  submitLabel = "Save Entry",
  loading = false,
}: JournalFormProps) {
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<JournalFormData>({
    resolver: zodResolver(journalSchema),
    defaultValues: {
      title: "",
      content: "",
      mood: undefined,
      ...defaultValues,
    },
  });

  const contentValue = watch("content") || "";
  const moodValue = watch("mood") as Mood | undefined;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <Input
        label="Title"
        placeholder="Give your entry a title..."
        error={errors.title?.message}
        {...register("title")}
      />

      <TextArea
        label="What's on your mind?"
        placeholder="Write freely about your thoughts, feelings, and experiences..."
        rows={8}
        maxLength={10000}
        currentLength={contentValue.length}
        error={errors.content?.message}
        {...register("content")}
      />

      <MoodSelector
        value={moodValue}
        onChange={(mood) => setValue("mood", mood, { shouldValidate: true })}
        error={errors.mood?.message}
      />

      <div className="flex justify-end pt-2">
        <Button type="submit" loading={loading} size="lg">
          {submitLabel}
        </Button>
      </div>
    </form>
  );
}
