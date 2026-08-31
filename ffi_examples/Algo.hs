-- Haskell — Algo.hs — SpiderLang FFI
module Algo where
import Data.List (sort, group)
import Data.Maybe (fromMaybe)
verify s = do putStrLn ("Haskell verify: " ++ s); return True
process xs = sort xs
validateBoard b = length b > 0
checksum s = sum (map fromEnum s) `mod` 256
partitionCheck p = p `elem` ["boot","recovery","vendor_boot"]
sizeToBytes n u = n * (1024 ^ u)
parseFstab ls = filter (not . null) $ map words ls
lunchCombos vs = filter ("userdebug" `isInfixOf`) vs
isInfixOf a b = a `elem` (map (take (length a)) (tails b))
tails [] = [[]]
tails xs@(_:xs') = xs : tails xs'
groupPartitions ps = group (sort ps)
a_bCheck f = "slotselect" `elem` words f
kernelOffset b = b + 0x8000
ramdiskOffset b = b + 0x01000000
tagsOffset b = b + 0x100
pageAlign s p = s `mod` p == 0
headerVersion v = v >= 0 && v <= 4
verifyHeader h = headerVersion (h `div` 100)
imageType t = t `elem` ["boot","recovery","vendor_boot","init_boot"]
flagMeaning f = fromMaybe "unknown" (lookup f [("kernel","kernel"),("ramdisk","ram")])
recoveryVariant v = v `elem` ["twrp","orangefox","pbrp","shrp"]
boardArch a = a `elem` ["arm64","arm","x86_64"]
validateSize s = s > 0 && s < 1024*1024*1024
toKB b = b `div` 1024
toMB b = b `div` (1024*1024)
toGB b = b `div` (1024*1024*1024)
fromKB k = k * 1024
fromMB m = m * 1024 * 1024
humanSize b | b < 1024 = show b ++ " B" | b < 1024*1024 = show (b `div` 1024) ++ " KB" | otherwise = show (b `div` (1024*1024)) ++ " MB"
