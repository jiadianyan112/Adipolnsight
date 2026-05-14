#!/usr/bin/env python3
import argparse, json, random, time, sys, os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--task-id", default="")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    time.sleep(0.5)

    metrics = {
        "liver_pdff": round(random.uniform(8.0, 15.0), 2),
        "visceral_fat_volume": round(random.uniform(2500, 5000), 1),
        "subcutaneous_fat_volume": round(random.uniform(5000, 8000), 1),
        "bone_marrow_fat_fraction": round(random.uniform(0.25, 0.45), 2),
        "dice_liver": round(random.uniform(0.90, 0.96), 2),
        "dice_visceral_fat": round(random.uniform(0.88, 0.94), 2),
        "dice_subcutaneous_fat": round(random.uniform(0.89, 0.95), 2),
        "dice_bone_marrow": round(random.uniform(0.87, 0.93), 2),
        "qc_status": "passed",
    }

    with open(os.path.join(args.output_dir, "segmentation_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    csv_path = os.path.join(args.output_dir, "fat_quantification.csv")
    with open(csv_path, "w") as f:
        f.write("subject_id,liver_pdff,visceral_fat_volume,subcutaneous_fat_volume,bone_marrow_fat_fraction\n")
        f.write(f"DEMO_001,{metrics['liver_pdff']},{metrics['visceral_fat_volume']},{metrics['subcutaneous_fat_volume']},{metrics['bone_marrow_fat_fraction']}\n")

    # Write placeholder PNG
    png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
    with open(os.path.join(args.output_dir, "overlay_preview.png"), "wb") as f:
        f.write(png)

    print(f"[mock_segmentation] Task {args.task_id} completed")
    output = {
        "task_id": args.task_id,
        "status": "success",
        "summary": metrics,
        "output_files": ["segmentation_metrics.json", "fat_quantification.csv", "overlay_preview.png"],
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
